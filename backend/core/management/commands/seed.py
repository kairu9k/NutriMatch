from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import SystemSetting
from nutrition.models import FoodExchangeCategory, FoodExchangeItem

# FNRI Food Exchange Lists for Meal Planning, 4th Edition (DOST-FNRI) —
# vault/Food Exchange Lists for Meal Planning.pdf. Category kcal/macros are
# the book's real Table 2.1-2.8 per-exchange values, not blended
# approximations — FNRI's own subgroup split (Rice A/B/C by protein; Meat
# Low/Medium/High Fat; Milk Whole/Low Fat/Non-fat) is preserved as distinct
# categories rather than flattened, since flattening loses real clinical
# information a rice/meat/milk-restricted diet plan needs.
FOOD_EXCHANGE_CATEGORIES = [
    {
        "code": "vegetable", "name": "Vegetable", "sort_order": 1,
        "kcal_per_exchange": Decimal("16"), "carbs_g": Decimal("3"), "protein_g": Decimal("1"), "fat_g": Decimal("0"),
        "color": "#2E7D32",
        "description": "Non-starchy vegetables. 1 exchange = 1/2 cup raw or cooked.",
    },
    {
        "code": "fruit", "name": "Fruit", "sort_order": 2,
        "kcal_per_exchange": Decimal("40"), "carbs_g": Decimal("10"), "protein_g": Decimal("0"), "fat_g": Decimal("0"),
        "color": "#E67E22",
        "description": "Fresh and processed fruit.",
    },
    {
        "code": "milk_whole", "name": "Milk (Whole)", "sort_order": 3,
        "kcal_per_exchange": Decimal("170"), "carbs_g": Decimal("12"), "protein_g": Decimal("8"), "fat_g": Decimal("10"),
        "color": "#5DADE2",
        "description": "Whole milk, 3.25% milk fat.",
    },
    {
        "code": "milk_lowfat", "name": "Milk (Low Fat)", "sort_order": 4,
        "kcal_per_exchange": Decimal("125"), "carbs_g": Decimal("12"), "protein_g": Decimal("8"), "fat_g": Decimal("5"),
        "color": "#5DADE2",
        "description": "Low fat milk, 1-2% milk fat.",
    },
    {
        "code": "milk_nonfat", "name": "Milk (Non-fat/Skim)", "sort_order": 5,
        "kcal_per_exchange": Decimal("80"), "carbs_g": Decimal("12"), "protein_g": Decimal("8"), "fat_g": Decimal("0"),
        "color": "#5DADE2",
        "description": "Non-fat, skim, or fat-free milk, under 1% milk fat.",
    },
    {
        "code": "rice_a", "name": "Rice A (Low Protein)", "sort_order": 6,
        "kcal_per_exchange": Decimal("92"), "carbs_g": Decimal("23"), "protein_g": Decimal("0"), "fat_g": Decimal("0"),
        "color": "#D4A017",
        "description": "Rice/cereal group with negligible protein content.",
    },
    {
        "code": "rice_b", "name": "Rice B (Medium Protein)", "sort_order": 7,
        "kcal_per_exchange": Decimal("100"), "carbs_g": Decimal("23"), "protein_g": Decimal("2"), "fat_g": Decimal("0"),
        "color": "#D4A017",
        "description": "Rice/cereal group with 2g protein per exchange.",
    },
    {
        "code": "rice_c", "name": "Rice C (High Protein)", "sort_order": 8,
        "kcal_per_exchange": Decimal("108"), "carbs_g": Decimal("23"), "protein_g": Decimal("4"), "fat_g": Decimal("0"),
        "color": "#D4A017",
        "description": "Rice/cereal/bread group with 4g protein per exchange.",
    },
    {
        "code": "meat_low", "name": "Meat (Low Fat)", "sort_order": 9,
        "kcal_per_exchange": Decimal("41"), "carbs_g": Decimal("0"), "protein_g": Decimal("8"), "fat_g": Decimal("1"),
        "color": "#C0392B",
        "description": "Lean meat, fish, seafood, legumes — 1g fat per exchange.",
    },
    {
        "code": "meat_medium", "name": "Meat (Medium Fat)", "sort_order": 10,
        "kcal_per_exchange": Decimal("86"), "carbs_g": Decimal("0"), "protein_g": Decimal("8"), "fat_g": Decimal("6"),
        "color": "#C0392B",
        "description": "Medium-fat meat, poultry, eggs — 6g fat per exchange.",
    },
    {
        "code": "meat_high", "name": "Meat (High Fat)", "sort_order": 11,
        "kcal_per_exchange": Decimal("122"), "carbs_g": Decimal("0"), "protein_g": Decimal("8"), "fat_g": Decimal("10"),
        "color": "#C0392B",
        "description": "High-fat meat and processed meat products — 10g fat per exchange.",
    },
    {
        "code": "fat", "name": "Fat", "sort_order": 12,
        "kcal_per_exchange": Decimal("45"), "carbs_g": Decimal("0"), "protein_g": Decimal("0"), "fat_g": Decimal("5"),
        "color": "#8E44AD",
        "description": "Oils, butter, nuts, and other fat sources.",
    },
    {
        "code": "sugar", "name": "Sugar", "sort_order": 13,
        "kcal_per_exchange": Decimal("20"), "carbs_g": Decimal("5"), "protein_g": Decimal("0"), "fat_g": Decimal("0"),
        "color": "#F4D03F",
        "description": "Sugar, syrups, and sweets.",
    },
]

# Real food items transcribed from the FNRI book's per-category tables
# (Filipino name, English name, household measure) — household_measure and
# ep_grams are the book's real "1 exchange" serving sizes. Dietary-safety
# flags (ok_for_diabetes/hypertension/renal, is_high_*) are added based on
# the book's own free-food/high-nutrient notes, not fabricated.
FOOD_EXCHANGE_ITEMS = {
    "vegetable": [
        {"name": "Kangkong (Swamp cabbage), leaves", "local_name": "Kangkong, dahon", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_fiber": True, "is_free_food": True},
        {"name": "Ampalaya (Bittermelon/gourd), leaves", "local_name": "Ampalaya, dahon", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_fiber": True, "is_free_food": True},
        {"name": "Sitaw (String/yard long bean), pod", "local_name": "Sitaw, bunga", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_fiber": True},
        {"name": "Kalabasa (Squash), fruit", "local_name": "Kalabasa, bunga", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_potassium": True},
        {"name": "Talong (Eggplant)", "local_name": "Talong", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_free_food": True},
        {"name": "Pechay (Pechay), leaves", "local_name": "Pechay, dahon", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_free_food": True},
        {"name": "Carrot", "local_name": "Carrot", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_potassium": True},
        {"name": "Broccoli", "local_name": "Broccoli", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_fiber": True},
        {"name": "Tomato, canned", "local_name": "Kamatis, de lata", "household_measure": "3/4 cup", "ep_grams": Decimal("110"), "is_high_sodium": True},
        {"name": "Mushroom, fresh", "local_name": "Kabuti, sariwa", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45")},
        {"name": "Malunggay (Horseradish tree), leaves", "local_name": "Malunggay, dahon", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_high_fiber": True, "is_free_food": True},
        {"name": "Toge (Mung bean sprout)", "local_name": "Toge", "household_measure": "1/2 cup raw or cooked", "ep_grams": Decimal("45"), "is_free_food": True},
    ],
    "fruit": [
        {"name": "Saging, lakatan (Banana, lacatan)", "local_name": "Saging, lakatan", "household_measure": "1/2 pc of 14 x 3.5 cm", "ep_grams": Decimal("40"), "is_high_potassium": True},
        {"name": "Saging, saba (Banana, saba)", "local_name": "Saging, saba", "household_measure": "1/2 pc of 12 x 4.5 cm", "ep_grams": Decimal("40"), "is_high_potassium": True},
        {"name": "Papaya, ripe", "local_name": "Papaya, hinog", "household_measure": "3/4 cup or 1 slice", "ep_grams": Decimal("90")},
        {"name": "Mangga, kalabaw, ripe (Mango, Manila super, ripe)", "local_name": "Mangga, kalabaw, hinog", "household_measure": "1/2 cup or 1 slice", "ep_grams": Decimal("70")},
        {"name": "Dalandan (Orange)", "local_name": "Dalandan", "household_measure": "3 pcs 6 cm diameter", "ep_grams": Decimal("155"), "is_high_potassium": True},
        {"name": "Pakwan (Watermelon)", "local_name": "Pakwan", "household_measure": "1 cup or 1 slice", "ep_grams": Decimal("150"), "is_high_potassium": True},
        {"name": "Pinya (Pineapple)", "local_name": "Pinya", "household_measure": "1/2 cup or 1 slice", "ep_grams": Decimal("80")},
        {"name": "Suha (Pomelo)", "local_name": "Suha", "household_measure": "2 segments", "ep_grams": Decimal("100"), "is_high_potassium": True},
        {"name": "Bayabas, red (Guava, red)", "local_name": "Bayabas, pula", "household_measure": "2 pcs 3.5 cm diameter each", "ep_grams": Decimal("60"), "is_high_fiber": True},
        {"name": "Coconut water", "local_name": "Niyog, tubig", "household_measure": "1 cup", "ep_grams": Decimal("240"), "is_high_potassium": True},
        {"name": "Chico (Sapodilla)", "local_name": "Chico", "household_measure": "1 pc 4 cm diameter", "ep_grams": Decimal("45")},
        {"name": "Mansanas, red (Apple, red)", "local_name": "Mansanas, pula", "household_measure": "1 pc 6 cm diameter", "ep_grams": Decimal("75")},
    ],
    "milk_whole": [
        {"name": "Milk, cow", "local_name": "Gatas, baka", "household_measure": "1 cup", "ep_grams": Decimal("250")},
        {"name": "Milk, powder, full cream", "local_name": "Gatas, pulbos, full cream", "household_measure": "5 Tbsp, level", "ep_grams": Decimal("35")},
        {"name": "Milk, evaporated", "local_name": "Gatas, evaporada", "household_measure": "1/2 cup", "ep_grams": Decimal("125")},
    ],
    "milk_lowfat": [
        {"name": "Milk, low fat", "local_name": "Gatas, low fat", "household_measure": "1 cup", "ep_grams": Decimal("250")},
        {"name": "Yogurt", "local_name": "Yogurt", "household_measure": "1/2 cup", "ep_grams": Decimal("150")},
    ],
    "milk_nonfat": [
        {"name": "Milk, skim", "local_name": "Gatas, skim", "household_measure": "1 cup", "ep_grams": Decimal("250")},
        {"name": "Milk, powder, skim", "local_name": "Gatas, pulbos, skim", "household_measure": "4 Tbsp, level", "ep_grams": Decimal("25")},
        {"name": "Yogurt, plain, skim", "local_name": "Yogurt, plain, skim", "household_measure": "1/2 cup", "ep_grams": Decimal("150")},
    ],
    "rice_a": [
        {"name": "Rice, \"protein-reduced\"", "local_name": "Kanin, \"protein-reduced\"", "household_measure": "1/3 cup", "ep_grams": Decimal("55"), "ok_for_renal": True},
        {"name": "Sweet potato (yellow, purple, white)", "local_name": "Kamote (dilaw, murado, puti)", "household_measure": "1 pc or 3/4 cup, cubed", "ep_grams": Decimal("85"), "is_high_fiber": True},
        {"name": "Cassava", "local_name": "Kamoteng kahoy/balinghoy", "household_measure": "1 slice or 3/4 cup, cubed", "ep_grams": Decimal("85")},
    ],
    "rice_b": [
        {"name": "Rice, well-milled, boiled", "local_name": "Bigas, maputi, sinaing", "household_measure": "1/2 cup", "ep_grams": Decimal("80")},
        {"name": "Rice, undermilled/brown rice, boiled", "local_name": "Pinawa, sinaing", "household_measure": "1/2 cup", "ep_grams": Decimal("80"), "is_high_fiber": True, "is_low_gi": True},
        {"name": "Corn on cob (yellow, white)", "local_name": "Mais sa busal (dilaw, puti)", "household_measure": "1/2 pc of 12.5 x 4 cm", "ep_grams": Decimal("65"), "is_high_fiber": True},
        {"name": "Potato", "local_name": "Patatas", "household_measure": "1 pc or 1 1/4 cup, cubed", "ep_grams": Decimal("170"), "is_high_potassium": True},
        {"name": "Bread, hamburger bun", "local_name": "Bread, hamburger bun", "household_measure": "1 pc", "ep_grams": Decimal("35"), "is_high_sodium": True},
    ],
    "rice_c": [
        {"name": "Bread, white, loaf", "local_name": "Loaf bread/Pan Amerikano", "household_measure": "2 pcs", "ep_grams": Decimal("35"), "is_high_sodium": True},
        {"name": "Bread, pan de sal", "local_name": "Pan de sal", "household_measure": "1 1/2 pcs", "ep_grams": Decimal("35"), "is_high_sodium": True},
        {"name": "Pasta (enriched/unenriched)", "local_name": "Pasta (enriched/unenriched)", "household_measure": "1/2 cup", "ep_grams": Decimal("70")},
    ],
    "meat_low": [
        {"name": "Chicken breast/white meat, no skin", "local_name": "Manok, laman", "household_measure": "1 slice", "ep_grams": Decimal("30"), "ok_for_renal": False},
        {"name": "Bangus (Milkfish)", "local_name": "Bangus", "household_measure": "1 slice", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Tilapia", "local_name": "Tilapia", "household_measure": "1/3 slice of 15.5 x 6 cm", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Tuna, yellow-fin", "local_name": "Tambakol", "household_measure": "1/3 slice", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Beef, lean meat", "local_name": "Laman", "household_measure": "1 slice, mbs", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Tofu (Soy bean curd)", "local_name": "Tokwa", "household_measure": "1 pc", "ep_grams": Decimal("70"), "is_low_gi": True, "ok_for_renal": False},
        {"name": "Mongo (Munggo), seeds, dried", "local_name": "Munggo (berde, dilaw, pula)", "household_measure": "1/2 cup", "ep_grams": Decimal("75"), "is_high_fiber": True, "ok_for_renal": False},
        {"name": "Shrimp, giant tiger prawn", "local_name": "Hipon, sugpo", "household_measure": "1/2 pc", "ep_grams": Decimal("40"), "ok_for_renal": False},
    ],
    "meat_medium": [
        {"name": "Chicken leg/drumstick", "local_name": "Manok, binti", "household_measure": "1 pc", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Egg, whole, chicken", "local_name": "Itlog, manok, buo", "household_measure": "1 pc medium", "ep_grams": Decimal("55"), "ok_for_renal": False},
        {"name": "Pork leg", "local_name": "Baboy, pata", "household_measure": "1 slice, mbs", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Cheese, cheddar, pasteurized, processed", "local_name": "Cheddar, pasteurized, processed", "household_measure": "1 slice", "ep_grams": Decimal("30"), "is_high_sodium": True, "ok_for_renal": False},
    ],
    "meat_high": [
        {"name": "Pork belly", "local_name": "Baboy, liempo, malaman", "household_measure": "1 slice", "ep_grams": Decimal("35"), "ok_for_renal": False},
        {"name": "Duck, whole egg (Balut)", "local_name": "Balut", "household_measure": "1 pc", "ep_grams": Decimal("65"), "ok_for_renal": False},
        {"name": "Sausage, frankfurter (Hotdog)", "local_name": "Hotdog, regular", "household_measure": "2 pcs", "ep_grams": Decimal("70"), "is_high_sodium": True, "ok_for_renal": False},
        {"name": "Peanuts, roasted, with skin", "local_name": "Mani, may balok, binusa", "household_measure": "2 Tbsp", "ep_grams": Decimal("20"), "is_high_potassium": True, "ok_for_renal": False},
    ],
    "fat": [
        {"name": "Oil (canola, corn, soybean, sunflower)", "local_name": "Mantika/Langis", "household_measure": "1 tsp", "ep_grams": Decimal("5")},
        {"name": "Oil, coconut", "local_name": "Mantika/Langis, niyog", "household_measure": "1 tsp", "ep_grams": Decimal("5")},
        {"name": "Avocado", "local_name": "Avocado", "household_measure": "12.5 x 6.5 x 2 cm", "ep_grams": Decimal("65"), "is_high_potassium": True},
        {"name": "Margarine", "local_name": "Mantekilya", "household_measure": "1 tsp", "ep_grams": Decimal("5"), "is_high_sodium": True},
        {"name": "Peanut butter", "local_name": "Peanut butter", "household_measure": "1/2 Tbsp", "ep_grams": Decimal("10"), "is_high_potassium": True},
        {"name": "Pork crackling, skin", "local_name": "Sitsaron baboy/Sitsarong balat", "household_measure": "5 pcs", "ep_grams": Decimal("10"), "is_high_sodium": True},
        {"name": "Coconut cream", "local_name": "Niyog, kakang gata", "household_measure": "1 Tbsp", "ep_grams": Decimal("15")},
    ],
    "sugar": [
        {"name": "Sugar (muscovado, brown, white)", "local_name": "Asukal (muscovado, pula, puti)", "household_measure": "1 tsp", "ep_grams": Decimal("5")},
        {"name": "Honey", "local_name": "Pulot-pukyutan", "household_measure": "1 tsp", "ep_grams": Decimal("5")},
        {"name": "Milk, sweetened, condensed, filled", "local_name": "Gatas, sweetened, kondensada, filled", "household_measure": "1 tsp", "ep_grams": Decimal("5"), "is_high_sodium": False},
        {"name": "Jam and jellies", "local_name": "Jam at jellies", "household_measure": "2 tsp", "ep_grams": Decimal("10")},
        {"name": "Leche flan (Creme custard)", "local_name": "Leche flan", "household_measure": "1 slice", "ep_grams": Decimal("10")},
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
