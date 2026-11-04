# Consultation only vs consultation + meal plan (2026-11-04, user's call).
# Bookings made before the choice existed included a meal plan, so they are
# marked consultation_meal_plan. Their invoices stay kind "consultation"
# (billing/0007), so they don't turn into unused meal-plan credits.

from django.db import migrations, models


def mark_existing(apps, schema_editor):
    # Requests the RND hasn't confirmed yet stay consultation only, so
    # confirming one never bills a package the client didn't choose.
    Appointment = apps.get_model("scheduling", "Appointment")
    Appointment.objects.exclude(status="pending").update(service="consultation_meal_plan")


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0010_call_presence_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='service',
            field=models.CharField(choices=[('consultation', 'Consultation only'), ('consultation_meal_plan', 'Consultation + meal plan')], default='consultation', max_length=30),
        ),
        migrations.RunPython(mark_existing, migrations.RunPython.noop),
    ]
