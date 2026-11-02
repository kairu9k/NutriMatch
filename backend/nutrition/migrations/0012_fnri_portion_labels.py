from decimal import Decimal

from django.db import migrations


def label(measure, ex):
    """Same as nutrition.plan_templates.portion_label (copied: migrations
    mustn't import code that can change)."""
    whole = int(ex)
    frac = ex - whole
    count = f"{whole or ''}½" if abs(frac - Decimal("0.5")) < Decimal("0.01") else f"{ex.normalize():f}"
    if not measure:
        return f"{count} exchange{'' if ex == 1 else 's'}"
    return measure if ex == 1 else f"{count} × {measure}"


def relabel(apps, schema_editor):
    """FNRI foods planned at more than (or less than) 1 exchange showed the
    1-exchange measure ("1/2 cup" for 2.5 exchanges). Rewrite only rows whose
    portion is still exactly that FNRI measure; anything an RND typed stays."""
    Item = apps.get_model("nutrition", "MealPlanFoodItem")
    for it in Item.objects.filter(food_item__isnull=False).exclude(exchanges=1).select_related("food_item"):
        base = (it.food_item.household_measure or "").strip()
        if it.exchanges and base and (it.household_measure or "").strip() == base:
            it.household_measure = label(base, Decimal(it.exchanges))
            it.save(update_fields=["household_measure"])


class Migration(migrations.Migration):
    dependencies = [("nutrition", "0011_meal_log_status_labels")]
    operations = [migrations.RunPython(relabel, migrations.RunPython.noop)]
