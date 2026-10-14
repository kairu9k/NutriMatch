"""Disease-specific diet templates (proposal objective 3): diabetes,
hypertension, renal disease and weight management.

A template turns a kcal target into a week of meals with the standard FNRI
food-exchange method:
  1. kcal × the condition's macro split → grams of carbohydrate/protein/fat;
  2. fixed vegetable/fruit/milk exchanges per condition, then rice exchanges
     fill the remaining carbohydrate, meat the remaining protein and fat
     exchanges the remaining fat (FNRI Food Exchange Lists, 4th ed., 2020);
  3. the day's exchanges are spread over 5 meals and filled with FNRI foods
     allowed for the condition (ok_for_* flags, low-GI first for diabetes,
     only low-protein Rice A starches for renal; no high-sodium foods for DASH, no
     high-K/P/Na foods for renal), varied by day, skipping foods that
     match the patient's recorded allergies.
The result is a DRAFT plan — the RND reviews and edits it in Meal Planning
before sending. Endpoints:
  GET  /api/rnd/relationships/<id>/meal-plan-templates/
  POST /api/rnd/relationships/<id>/meal-plans/from-template/ {template, target_kcal?}
"""

from datetime import time
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

from .models import FoodExchangeItem, MealPlan, MealPlanFoodItem, MealPlanMeal

TEMPLATES = {
    "diabetes": {
        "label": "Diabetes mellitus", "condition": MealPlan.Condition.DIABETES, "split": (50, 20, 30),
        "veg": 4, "fruit": 3, "milk": 1, "milk_code": "milk_nonfat", "sugar": 0,
        "rice_codes": ["rice_b", "rice_a"], "meat_codes": ["meat_low"], "flag": "ok_for_diabetes",
        "description": "Consistent carbohydrate at every meal, low-GI rice and root crops first, no added sugar.",
        "guidance": "Keep carbohydrate portions the same each day; choose brown/undermilled rice, root crops and whole fruit "
                    "over juice; no sweetened drinks or desserts; pair every snack with fiber or protein.",
    },
    "hypertension": {
        "label": "Hypertension (DASH)", "condition": MealPlan.Condition.HYPERTENSION, "split": (55, 18, 27),
        "veg": 5, "fruit": 4, "milk": 2, "milk_code": "milk_lowfat", "sugar": 0,
        "rice_codes": ["rice_b", "rice_c"], "meat_codes": ["meat_low"], "flag": "ok_for_hypertension",
        "avoid": ["is_high_sodium"],
        "description": "DASH-style: more vegetables, fruit and low-fat milk; lean protein; low sodium.",
        "guidance": "Sodium under 2,000 mg/day: no patis, toyo, bagoong, instant noodles or processed meats. Flavor with "
                    "calamansi, garlic, ginger and onion. Plenty of vegetables and fruit every day.",
    },
    "renal": {
        "label": "Renal disease (CKD, not on dialysis)", "condition": MealPlan.Condition.RENAL, "split": (60, 10, 30),
        "veg": 3, "fruit": 2, "milk": 0, "milk_code": "milk_nonfat", "sugar": 1,
        "rice_codes": ["rice_a"], "meat_codes": ["meat_low"], "flag": "ok_for_renal",
        "avoid": ["is_high_potassium", "is_high_phosphorus", "is_high_sodium"],
        "description": "Protein-restricted with enough energy; low-potassium, low-phosphorus foods; no milk.",
        "guidance": "Limit protein to the plan; avoid high-potassium fruits/vegetables (banana, mango, malunggay), dairy and "
                    "processed foods (phosphorus). Leach vegetables (soak and boil) and follow any fluid limit from the doctor.",
    },
    "weight_management": {
        "label": "Weight management", "condition": MealPlan.Condition.WEIGHT_LOSS, "split": (45, 25, 30),
        "veg": 5, "fruit": 3, "milk": 1, "milk_code": "milk_nonfat", "sugar": 0,
        "rice_codes": ["rice_b", "rice_c"], "meat_codes": ["meat_low"], "flag": None,
        "description": "Calorie deficit with higher protein and lots of vegetables to stay full.",
        "guidance": "Half the plate vegetables, a quarter rice, a quarter lean protein. One cup of rice per meal at most; "
                    "water instead of sweetened drinks; avoid fried and fatty dishes.",
    },
}

SLOTS = [  # (meal slot, time, share of each group: rice, meat, veg, fruit, fat)
    ("breakfast", time(7), {"rice": .30, "meat": .20, "veg": 0, "fruit": .25, "fat": .20}),
    ("am_snack", time(10), {"rice": 0, "meat": 0, "veg": 0, "fruit": .35, "fat": 0}),
    ("lunch", time(12), {"rice": .35, "meat": .40, "veg": .50, "fruit": 0, "fat": .40}),
    ("pm_snack", time(15, 30), {"rice": 0, "meat": 0, "veg": 0, "fruit": .40, "fat": 0}),
    ("dinner", time(19), {"rice": .35, "meat": .40, "veg": .50, "fruit": 0, "fat": .40}),
]
# never picked by a template: very high fat / sodium items an RND would rarely prescribe
SKIP_NAMES = ("pork crackling", "coconut cream", "margarine", "sausage", "pork belly", "balut", "leche flan", "condensed")
MIN_KCAL, MAX_KCAL = 800, 5000
HALF = Decimal("0.5")


def _half(x):
    """Round to the nearest half exchange (FNRI lists use ½ exchanges)."""
    return (Decimal(str(max(x, 0))) / HALF).quantize(Decimal("1"), ROUND_HALF_UP) * HALF


def daily_exchanges(tpl, kcal):
    carb_pct, prot_pct, fat_pct = tpl["split"]
    carb_g, prot_g, fat_g = kcal * carb_pct / 100 / 4, kcal * prot_pct / 100 / 4, kcal * fat_pct / 100 / 9
    veg, fruit, milk, sugar = tpl["veg"], tpl["fruit"], tpl["milk"], tpl["sugar"]
    milk_fat = {"milk_nonfat": 0, "milk_lowfat": 5, "milk_whole": 10}[tpl["milk_code"]]
    rice = (carb_g - veg * 3 - fruit * 10 - milk * 12 - sugar * 5) / 23
    rice_protein = 0 if tpl["rice_codes"][0] == "rice_a" else 2
    meat = (prot_g - veg * 1 - milk * 8 - rice * rice_protein) / 8
    fat = (fat_g - meat * 1 - milk * milk_fat) / 5
    return {"rice": _half(rice), "meat": _half(meat), "veg": _half(veg), "fruit": _half(fruit),
            "milk": _half(milk), "fat": _half(fat), "sugar": _half(sugar)}


def split_over_slots(total, group):
    """Spread a day's exchanges over the meals; the last meal that gets this
    group takes the remainder so the day adds up exactly."""
    shares = [(slot, s[group]) for slot, _, s in SLOTS if s[group]]
    out, used = {}, Decimal("0")
    for i, (slot, share) in enumerate(shares):
        amount = total - used if i == len(shares) - 1 else _half(float(total) * share)
        amount = max(amount, Decimal("0"))
        out[slot] = amount
        used += amount
    return out


# Food words each onboarding allergy choice covers (ClientOnboarding.vue
# ALLERGY_OPTIONS; mirrored in frontend utils/foodWarnings.js). Matched as
# whole words, so "egg" doesn't catch "Eggplant" nor "milk" "Milkfish".
ALLERGEN_WORDS = {
    "shrimp / shellfish": ["shrimp", "prawn", "crab", "lobster", "squid", "clam", "mussel", "oyster", "scallop",
                           "shellfish", "hipon", "alimango", "talaba", "tahong", "pusit"],
    "fish": ["fish", "milkfish", "bangus", "tilapia", "tuna", "sardine", "galunggong", "mackerel", "dilis", "tuyo"],
    "peanuts": ["peanut"],
    "tree nuts": ["cashew", "almond", "walnut", "pili", "pistachio", "hazelnut", "macadamia"],
    "eggs": ["egg", "balut", "leche flan", "custard"],
    "milk": ["milk", "cheese", "yogurt", "leche flan", "custard"],
    "soy": ["soy", "tofu", "tokwa", "taho"],
    "wheat / gluten": ["wheat", "gluten", "bread", "pan de sal", "pasta", "noodle", "flour", "bun"],
}


def allergen_patterns(allergies):
    """Whole-word patterns for a client's allergies: the words a listed
    choice covers, or a typed allergy split on "/" and "," (plural s optional)."""
    import re

    words = []
    for a in allergies or []:
        text = str(a).strip().lower()
        if not text:
            continue
        words += ALLERGEN_WORDS.get(text) or [w.strip() for w in re.split(r"[/,]", text) if w.strip()]
    pats = []
    for w in dict.fromkeys(words):
        stem = w[:-1] if w.endswith("s") and len(w) > 3 else w
        pats.append(re.compile(r"\b" + re.escape(stem) + r"(e?s)?\b"))
    return pats


def _allergens(health):
    return allergen_patterns(getattr(health, "allergies", None))


def candidates(tpl, codes, allergens):
    items = FoodExchangeItem.objects.filter(category__code__in=codes).select_related("category").order_by("id")
    renal_protein = tpl["condition"] == MealPlan.Condition.RENAL and any(c.startswith("meat") for c in codes)
    if renal_protein:
        # CKD limits the AMOUNT of protein (the exchange math already does) but
        # still needs some — the FNRI "ok for renal" flag excludes every meat,
        # so pick the lower-potassium / lower-phosphorus ones instead.
        lower = items.filter(is_high_potassium=False, is_high_phosphorus=False)
        items = lower if lower.exists() else items
    elif tpl["flag"]:
        items = items.filter(**{tpl["flag"]: True})
    # The FNRI "ok for" flags don't cover everything (every food is "ok for
    # hypertension", bananas are "ok for renal"), so also leave out the foods
    # the Meal Planning warnings flag (utils/foodWarnings.js) — unless that
    # would leave nothing to choose from.
    for field in tpl.get("avoid", []):
        kept = items.filter(**{field: False})
        if kept.exists():
            items = kept
    out = []
    for code in codes:  # keep the template's preference order between categories
        for it in items:
            if it.category.code != code:
                continue
            name = f"{it.name} {it.local_name or ''}".lower()
            if any(s in name for s in SKIP_NAMES) or any(p.search(name) for p in allergens):
                continue
            out.append(it)
    if tpl["condition"] == MealPlan.Condition.DIABETES:
        out.sort(key=lambda it: (not it.is_low_gi,))  # stable: low-GI first, preference order kept
    return out


def suggested_kcal(rel, key=None):
    """The plan's starting kcal: the latest finalized NCP prescription, else the
    latest draft's, else the screening TDEE (minus 500 kcal, min 1,200, for
    weight management)."""
    from clinical.models import NcpRecord, PreConsultationScreening

    recs = NcpRecord.objects.filter(relationship=rel, target_kcal__isnull=False).order_by("-encounter_date", "-created_at")
    rec = recs.filter(status=NcpRecord.Status.COMPLETED).first() or recs.first()
    if rec:
        return {"value": int(rec.target_kcal), "source": f"NCP record of {rec.encounter_date:%b} {rec.encounter_date.day}"}
    s = PreConsultationScreening.objects.filter(client=rel.client).order_by("-created_at").first()
    if s and s.tdee_kcal:
        tdee = float(s.tdee_kcal)
        if key == "weight_management":
            return {"value": int(max(1200, round((tdee - 500) / 50) * 50)), "source": "screening TDEE − 500 kcal"}
        return {"value": int(round(tdee / 50) * 50), "source": "screening TDEE"}
    return {"value": 1800, "source": "default — no NCP target or screening yet"}


def build_plan_from_template(rel, key, kcal):
    tpl = TEMPLATES[key]
    health = getattr(rel.client, "health_profile", None)
    allergens = _allergens(health)
    day = daily_exchanges(tpl, kcal)
    pools = {
        "rice": candidates(tpl, tpl["rice_codes"], allergens),
        "meat": candidates(tpl, tpl["meat_codes"], allergens),
        "veg": candidates(tpl, ["vegetable"], allergens),
        "fruit": candidates(tpl, ["fruit"], allergens),
        "milk": candidates(tpl, [tpl["milk_code"]], allergens),
        "fat": candidates(tpl, ["fat"], allergens),
        "sugar": candidates(tpl, ["sugar"], allergens),
    }
    per_slot = {g: split_over_slots(day[g], g) for g in ("rice", "meat", "veg", "fruit", "fat")}
    per_slot["milk"] = {"breakfast": day["milk"]} if day["milk"] else {}
    per_slot["sugar"] = {"pm_snack": day["sugar"]} if day["sugar"] else {}

    carb_pct, prot_pct, fat_pct = tpl["split"]
    restrictions = [f"Allergies: {', '.join(health.allergies)}"] if health and health.allergies else []
    with transaction.atomic():
        plan = MealPlan.objects.create(
            relationship=rel, name=f"{tpl['label']} plan — {kcal:,} kcal", condition=tpl["condition"],
            target_kcal=Decimal(kcal), target_carb_g=Decimal(round(kcal * carb_pct / 100 / 4)),
            target_protein_g=Decimal(round(kcal * prot_pct / 100 / 4)), target_fat_g=Decimal(round(kcal * fat_pct / 100 / 9)),
            total_rice=day["rice"], total_meat=day["meat"], total_vegetable=day["veg"], total_fruit=day["fruit"],
            total_milk=day["milk"], total_fat=day["fat"], total_sugar=day["sugar"],
            notes=tpl["guidance"], allergies_restrictions="; ".join(restrictions) or None,
            status=MealPlan.Status.DRAFT,
        )
        for d in range(7):
            for si, (slot, at, _) in enumerate(SLOTS):
                meal = MealPlanMeal.objects.create(meal_plan=plan, day_of_week=d, meal_time=slot, scheduled_time=at)
                for group in ("rice", "meat", "veg", "fruit", "milk", "fat", "sugar"):
                    ex = per_slot[group].get(slot, Decimal("0"))
                    pool = pools[group]
                    if not ex or not pool:
                        continue
                    item = pool[(d + si * 2) % len(pool)]
                    cat = item.category
                    MealPlanFoodItem.objects.create(
                        meal_plan_meal=meal, food_item=item, food_name=item.name,
                        source_type=MealPlanFoodItem.SourceType.FEL, exchanges=ex, household_measure=item.household_measure,
                        kcal=cat.kcal_per_exchange * ex, carbs_g=(cat.carbs_g or 0) * ex,
                        protein_g=(cat.protein_g or 0) * ex, fat_g=(cat.fat_g or 0) * ex,
                    )
                meal.recompute_exchanges()
    return plan


# ---------------------------------------------------------------- API
class TemplateRequestSerializer(serializers.Serializer):
    template = serializers.ChoiceField(choices=list(TEMPLATES))
    target_kcal = serializers.IntegerField(min_value=MIN_KCAL, max_value=MAX_KCAL, required=False)


def _rel(request, pk):
    from scheduling.models import RndClientRelationship

    return get_object_or_404(RndClientRelationship.objects.select_related("client__health_profile"), pk=pk, rnd=request.user)


class MealPlanTemplateListView(APIView):
    permission_classes = [IsRnd]

    def get(self, request, relationship_id):
        rel = _rel(request, relationship_id)
        health = getattr(rel.client, "health_profile", None)
        return Response({
            "templates": [
                {"key": k, "label": t["label"], "description": t["description"], "condition": t["condition"],
                 "split": {"carbs": t["split"][0], "protein": t["split"][1], "fat": t["split"][2]}}
                for k, t in TEMPLATES.items()
            ],
            "suggested_kcal": suggested_kcal(rel),
            "allergies": (health.allergies if health else None) or [],
            "min_kcal": MIN_KCAL, "max_kcal": MAX_KCAL,
        })


class MealPlanFromTemplateView(APIView):
    permission_classes = [IsRnd]

    def post(self, request, relationship_id):
        from scheduling.discharge import ensure_open

        from .serializers import MealPlanSerializer

        rel = _rel(request, relationship_id)
        ensure_open(rel)
        data = TemplateRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        key = data.validated_data["template"]
        kcal = data.validated_data.get("target_kcal") or suggested_kcal(rel, key)["value"]
        kcal = max(MIN_KCAL, min(MAX_KCAL, int(kcal)))
        plan = build_plan_from_template(rel, key, kcal)
        plan = MealPlan.objects.prefetch_related("meals__food_items").get(pk=plan.pk)
        return Response(MealPlanSerializer(plan, context={"request": request}).data, status=status.HTTP_201_CREATED)
