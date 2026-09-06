from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import SystemSetting
from nutrition.models import FoodExchangeCategory, FoodExchangeItem

# FNRI Food Exchange List (4th Ed.) — the 6 canonical exchange groups used
# throughout this project's meal-planning schema (MealPlanMeal's
# rice/meat/vegetable/fruit/milk/fat_exchanges fields). Per-exchange kcal
# and macros are the FNRI FEL standard values for one exchange unit.
FOOD_EXCHANGE_CATEGORIES = [
    {
        "code": "rice", "name": "Rice / Cereals", "sort_order": 1,
        "kcal_per_exchange": Decimal("100"), "carbs_g": Decimal("23"), "protein_g": Decimal("2"), "fat_g": Decimal("0"),
        "color": "#D4A017",
        "description": "Rice, cereals, root crops, and other carbohydrate staples.",
    },
    {
        "code": "meat", "name": "Meat / Fish / Poultry", "sort_order": 2,
        "kcal_per_exchange": Decimal("75"), "carbs_g": Decimal("0"), "protein_g": Decimal("8"), "fat_g": Decimal("3"),
        "color": "#C0392B",
        "description": "Meat, poultry, fish, eggs, and other protein sources (medium-fat class).",
    },
    {
        "code": "vegetable", "name": "Vegetable", "sort_order": 3,
        "kcal_per_exchange": Decimal("25"), "carbs_g": Decimal("5"), "protein_g": Decimal("1"), "fat_g": Decimal("0"),
        "color": "#2E7D32",
        "description": "Non-starchy vegetables.",
    },
    {
        "code": "fruit", "name": "Fruit", "sort_order": 4,
        "kcal_per_exchange": Decimal("50"), "carbs_g": Decimal("13"), "protein_g": Decimal("0"), "fat_g": Decimal("0"),
        "color": "#E67E22",
        "description": "Fresh fruit.",
    },
    {
        "code": "milk", "name": "Milk", "sort_order": 5,
        "kcal_per_exchange": Decimal("110"), "carbs_g": Decimal("12"), "protein_g": Decimal("8"), "fat_g": Decimal("4"),
        "color": "#5DADE2",
        "description": "Milk and dairy products (whole milk class).",
    },
    {
        "code": "fat", "name": "Fat", "sort_order": 6,
        "kcal_per_exchange": Decimal("45"), "carbs_g": Decimal("0"), "protein_g": Decimal("0"), "fat_g": Decimal("5"),
        "color": "#8E44AD",
        "description": "Oils, butter, nuts, and other fat sources.",
    },
]

# A small, real starter set of common Filipino food items per category —
# household_measure and ep_grams are FNRI FEL standard serving sizes for
# one exchange unit. Only food_name-equivalent data (RA 10173 data
# minimization) — no nutrient payload duplicated beyond what the category
# itself already carries.
FOOD_EXCHANGE_ITEMS = {
    "rice": [
        {"name": "Rice, cooked", "local_name": "Kanin", "household_measure": "1/2 cup", "ep_grams": Decimal("100")},
        {"name": "Corn, whole kernel", "local_name": "Mais", "household_measure": "1/2 cup", "ep_grams": Decimal("90")},
        {"name": "Bread, white", "local_name": "Tinapay", "household_measure": "1 slice", "ep_grams": Decimal("25"), "is_high_sodium": True},
        {"name": "Camote (sweet potato), boiled", "local_name": "Kamote", "household_measure": "1 medium", "ep_grams": Decimal("100"), "is_high_fiber": True},
        {"name": "Saba banana, boiled", "local_name": "Saba", "household_measure": "3 pcs small", "ep_grams": Decimal("100")},
    ],
    "meat": [
        {"name": "Chicken breast, no skin", "local_name": "Dibdib ng manok", "household_measure": "1 matchbox size", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Bangus (milkfish)", "local_name": "Bangus", "household_measure": "1/3 medium", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Tilapia", "local_name": "Tilapia", "household_measure": "1 slice", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Egg, whole", "local_name": "Itlog", "household_measure": "1 pc", "ep_grams": Decimal("50"), "ok_for_renal": False},
        {"name": "Tofu (tokwa)", "local_name": "Tokwa", "household_measure": "1 slice", "ep_grams": Decimal("70"), "is_low_gi": True},
        {"name": "Mongo beans, cooked", "local_name": "Munggo", "household_measure": "1/2 cup", "ep_grams": Decimal("90"), "is_high_fiber": True, "ok_for_renal": False},
    ],
    "vegetable": [
        {"name": "Kangkong (water spinach)", "local_name": "Kangkong", "household_measure": "1 cup", "ep_grams": Decimal("100"), "is_high_fiber": True, "is_free_food": True},
        {"name": "Ampalaya (bitter gourd)", "local_name": "Ampalaya", "household_measure": "1 cup", "ep_grams": Decimal("100"), "is_high_fiber": True, "is_free_food": True},
        {"name": "Sitaw (string beans)", "local_name": "Sitaw", "household_measure": "1 cup", "ep_grams": Decimal("100"), "is_high_fiber": True, "is_free_food": True},
        {"name": "Kalabasa (squash)", "local_name": "Kalabasa", "household_measure": "1 cup", "ep_grams": Decimal("100"), "is_high_potassium": True},
        {"name": "Talong (eggplant)", "local_name": "Talong", "household_measure": "1 cup", "ep_grams": Decimal("100"), "is_free_food": True},
    ],
    "fruit": [
        {"name": "Saging na lakatan (banana)", "local_name": "Saging", "household_measure": "1 small", "ep_grams": Decimal("80"), "is_high_potassium": True},
        {"name": "Papaya, ripe", "local_name": "Papaya", "household_measure": "1 slice", "ep_grams": Decimal("120")},
        {"name": "Mangga, ripe (mango)", "local_name": "Mangga", "household_measure": "1/2 medium", "ep_grams": Decimal("65")},
        {"name": "Dalandan (orange)", "local_name": "Dalandan", "household_measure": "1 medium", "ep_grams": Decimal("100"), "is_high_potassium": True},
        {"name": "Watermelon", "local_name": "Pakwan", "household_measure": "1 cup diced", "ep_grams": Decimal("150"), "is_high_potassium": True},
    ],
    "milk": [
        {"name": "Milk, fresh whole", "local_name": "Gatas", "household_measure": "1 cup", "ep_grams": Decimal("240")},
        {"name": "Milk, skim/low-fat", "local_name": "Gatas na walang taba", "household_measure": "1 cup", "ep_grams": Decimal("240")},
        {"name": "Yogurt, plain", "local_name": "Yogurt", "household_measure": "1 cup", "ep_grams": Decimal("240")},
    ],
    "fat": [
        {"name": "Cooking oil (vegetable/canola)", "local_name": "Mantika", "household_measure": "1 tsp", "ep_grams": Decimal("5")},
        {"name": "Peanuts, roasted", "local_name": "Mani", "household_measure": "10 pcs", "ep_grams": Decimal("10"), "is_high_potassium": True},
        {"name": "Margarine", "local_name": "Margarina", "household_measure": "1 tsp", "ep_grams": Decimal("5"), "is_high_sodium": True},
    ],
}

DEFAULT_SETTINGS = [
    {"key": "platform_commission_pct", "value": "10.00", "description": "Default platform commission percentage applied to new invoices."},
    {"key": "platform_name", "value": "NutriMatch", "description": "Display name used in emails and notifications."},
    {"key": "support_email", "value": "support@nutrimatch.ph", "description": "Contact email shown to users for support inquiries."},
]


class Command(BaseCommand):
    help = "Seeds reference data every dev environment needs: FNRI food exchange categories/items and default system settings. Idempotent — safe to re-run."

    def handle(self, *args, **options):
        self._seed_food_exchange()
        self._seed_system_settings()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_food_exchange(self):
        created_categories = 0
        created_items = 0

        for cat_data in FOOD_EXCHANGE_CATEGORIES:
            code = cat_data["code"]
            category, created = FoodExchangeCategory.objects.update_or_create(
                code=code, defaults={k: v for k, v in cat_data.items() if k != "code"},
            )
            if created:
                created_categories += 1

            for item_data in FOOD_EXCHANGE_ITEMS.get(code, []):
                _, item_created = FoodExchangeItem.objects.update_or_create(
                    category=category, name=item_data["name"],
                    defaults={k: v for k, v in item_data.items() if k != "name"},
                )
                if item_created:
                    created_items += 1

        self.stdout.write(
            f"Food exchange: {created_categories} categories created, "
            f"{FoodExchangeCategory.objects.count()} total; "
            f"{created_items} items created, {FoodExchangeItem.objects.count()} total."
        )

    def _seed_system_settings(self):
        created_settings = 0
        for setting in DEFAULT_SETTINGS:
            _, created = SystemSetting.objects.get_or_create(
                key=setting["key"], defaults={"value": setting["value"], "description": setting["description"]},
            )
            if created:
                created_settings += 1

        self.stdout.write(f"System settings: {created_settings} created, {SystemSetting.objects.count()} total.")
