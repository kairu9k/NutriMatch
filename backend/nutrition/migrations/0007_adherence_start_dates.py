"""Adherence keeps its history when an edited plan is re-sent.

- MealPlan.first_sent_at: when the patient first got the plan. Backfilled
  from the earlier of sent_at and the plan's first meal log, which also
  restores plans whose sent_at was already moved by a re-send.
- MealPlanMeal.created_at: added nullable first so existing meals stay null
  ("counts from the plan's start"), then given its default for new meals.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

import django.utils.timezone
from django.db import migrations, models

PH = ZoneInfo("Asia/Manila")


def backfill_first_sent(apps, schema_editor):
    MealPlan = apps.get_model("nutrition", "MealPlan")
    MealLog = apps.get_model("nutrition", "MealLog")
    for plan in MealPlan.objects.exclude(sent_at__isnull=True):
        first = plan.sent_at
        log = MealLog.objects.filter(meal_plan_meal__meal_plan=plan).order_by("log_date").values_list("log_date", flat=True).first()
        if log:
            first = min(first, datetime.combine(log, time.min, tzinfo=PH))
        plan.first_sent_at = first
        plan.save(update_fields=["first_sent_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("nutrition", "0006_meal_plan_food_grams"),
    ]

    operations = [
        migrations.AddField(
            model_name="mealplan",
            name="first_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mealplanmeal",
            name="created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="mealplanmeal",
            name="created_at",
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
        migrations.RunPython(backfill_first_sent, migrations.RunPython.noop),
    ]
