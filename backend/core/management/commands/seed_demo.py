"""Demo data for manual testing and the capstone defense.

    python manage.py seed_demo           # create the demo set (skips if already there)
    python manage.py seed_demo --reset   # delete every demo account + its activity, then re-create

5 RNDs and 5 clients, each at a different point in the journey (see RNDS /
CLIENTS below). All demo accounts use the @nutrimatch.test domain (can't
receive mail), are already email-verified, and share one password:
DEMO_PASSWORD from .env (default below). Dev-only — refuses to run with
DEBUG=False unless --force is passed.

Clinical numbers (BMI, BMR, TDEE, NRS-2002) are computed with the same
clinical/services.py functions the app uses, never typed in, and paid
invoices go through billing.services.record_successful_payment() like a
real PayMongo payment does. Dates are relative to "today" in Philippine
time, so the data always looks current.
"""
import secrets
import struct
import zlib
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

from decouple import config
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from billing.models import Invoice
from billing.services import record_successful_payment
from clinical.models import NcpRecord, PreConsultationScreening, ProgressRecord
from clinical.services import (
    calculate_bmi,
    calculate_bmr_mifflin_st_jeor,
    calculate_nrs2002,
    calculate_tdee,
    classify_bmi_asia_pacific,
)
from communication.models import Message
from communication.services import notify
from core.models import SystemSetting
from nutrition.models import FoodExchangeItem, MealLog, MealPlan, MealPlanFoodItem, MealPlanMeal
from profiles.models import (
    ClientHealthProfile,
    ClientProfile,
    RndAvailabilitySchedule,
    RndLanguage,
    RndProfile,
)
from scheduling.models import Appointment, ConsultationSession, Review, RndClientRelationship
from scheduling.services import JitsiVideoService

MANILA = ZoneInfo("Asia/Manila")
DEMO_DOMAIN = "nutrimatch.test"
DEFAULT_DEMO_PASSWORD = "NutriMatchDemo1!"

LANGUAGE_NAMES = {"en": "English", "fil": "Filipino", "ceb": "Cebuano"}

# day_of_week uses the app's convention: Sunday=0 … Saturday=6.
RNDS = [
    {
        "key": "maria", "first_name": "Maria", "last_name": "Santos",
        "specialization": "Diabetes & Weight Management",
        "bio": "Registered Nutritionist-Dietitian with 8 years of clinical experience helping Filipino adults manage type 2 diabetes and lose weight through practical, rice-aware meal plans.",
        "fee": Decimal("800"), "modes": ["video", "chat", "in_person"], "languages": ["en", "fil", "ceb"],
        "availability": [(d, time(9), time(17)) for d in (1, 2, 3, 4, 5)],
        "verified": True, "accepting": True, "prc": "0123456",
    },
    {
        "key": "jose", "first_name": "Jose", "last_name": "Reyes",
        "specialization": "Renal & Hypertension Nutrition",
        "bio": "Hospital-based RND focused on kidney disease and blood pressure control. Specializes in low-sodium, potassium-aware Filipino diets.",
        "fee": Decimal("1000"), "modes": ["video"], "languages": ["en", "fil"],
        "availability": [(d, time(13), time(18)) for d in (2, 4, 6)],
        "verified": True, "accepting": True, "prc": "0234567",
    },
    {
        "key": "angela", "first_name": "Angela", "last_name": "Villanueva",
        "specialization": "Sports Nutrition",
        "bio": "Works with athletes and active adults on performance nutrition, body composition and recovery. Currently at full capacity.",
        "fee": Decimal("600"), "modes": ["video", "chat"], "languages": ["en", "fil"],
        "availability": [(d, time(8), time(12)) for d in (1, 3, 5)],
        "verified": True, "accepting": False, "prc": "0345678",
    },
    {
        "key": "ramon", "first_name": "Ramon", "last_name": "Dela Cruz",
        "specialization": "Pediatric & General Nutrition",
        "bio": "Community nutritionist in Davao City. Helps families with child growth, picky eating and healthy home cooking on a budget.",
        "fee": Decimal("700"), "modes": ["video", "in_person"], "languages": ["ceb", "fil", "en"],
        "availability": [(d, time(10), time(16)) for d in (1, 2, 3, 4, 5, 6)],
        "verified": True, "accepting": True, "prc": "0456789",
    },
    {
        "key": "kristine", "first_name": "Kristine", "last_name": "Bautista",
        "specialization": "Cardiovascular Nutrition",
        "bio": "Newly registered RND focused on heart-healthy eating and cholesterol management.",
        "fee": Decimal("750"), "modes": ["video", "chat"], "languages": ["en", "fil"],
        "availability": [(d, time(9), time(15)) for d in (1, 3, 5)],
        "verified": False, "accepting": True, "prc": None,  # pending admin review — has a license photo instead
    },
]

CLIENTS = [
    {"key": "ana", "first_name": "Ana", "last_name": "Cruz", "dob": date(1998, 4, 12), "sex": "female",
     "conditions": ["Weight Management"], "goals": ["Lose weight"]},
    {"key": "benjamin", "first_name": "Benjamin", "last_name": "Garcia", "dob": date(1995, 3, 10), "sex": "male",
     "conditions": ["Obesity Management"], "goals": ["Lose weight", "Lower blood sugar"]},
    {"key": "carla", "first_name": "Carla", "last_name": "Mendoza", "dob": date(1983, 9, 2), "sex": "female",
     "conditions": ["Type 2 Diabetes"], "goals": ["Control blood sugar", "Lose weight"],
     "allergies": ["Shrimp"]},
    {"key": "daniel", "first_name": "Daniel", "last_name": "Torres", "dob": date(1970, 1, 20), "sex": "male",
     "conditions": ["Hypertension"], "goals": ["Lower blood pressure"],
     "restrictions": ["Low sodium"]},
    {"key": "elena", "first_name": "Elena", "last_name": "Ramos", "dob": date(1995, 11, 5), "sex": "female",
     "conditions": ["Other"], "goals": ["Healthier family meals"]},
]


def demo_email(first_name, last_name):
    return f"{first_name}.{last_name}".lower().replace(" ", "") + f"@{DEMO_DOMAIN}"


def all_demo_emails():
    return [demo_email(p["first_name"], p["last_name"]) for p in RNDS + CLIENTS]


def dow(d: date) -> int:
    """Python's weekday (Mon=0) → the app's day_of_week (Sun=0)."""
    return (d.weekday() + 1) % 7


def at(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=MANILA)


def shift_to_day(start: date, allowed_days, step: int) -> date:
    """First date from `start` (inclusive), moving by `step` days, whose
    day_of_week is one of `allowed_days` — keeps demo appointments inside
    the RND's real availability."""
    d = start
    while dow(d) not in allowed_days:
        d += timedelta(days=step)
    return d


def placeholder_license_png() -> BytesIO:
    """A tiny valid PNG (a grey ID-card shape) so the pending RND has a
    license photo for the admin to review. Built by hand — Pillow isn't a
    dependency."""
    w, h = 120, 76
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            header = y < 16
            photo = 10 <= x < 42 and 26 <= y < 66
            line = 52 <= x < 110 and y in (32, 33, 44, 45, 56, 57)
            shade = (27, 94, 32) if header else (190, 190, 190) if photo else (120, 120, 120) if line else (244, 242, 236)
            row.extend(shade)
        rows.append(bytes(row))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")
    buf = BytesIO(png)
    buf.name = "demo-prc-license.png"
    return buf


class Command(BaseCommand):
    help = "Create (or with --reset, rebuild) the 5-RND / 5-client demo data set."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all demo accounts and their activity first.")
        parser.add_argument("--force", action="store_true", help="Allow running with DEBUG=False.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("seed_demo creates accounts with a shared known password — refusing with DEBUG=False (use --force).")

        self.password = config("DEMO_PASSWORD", default=DEFAULT_DEMO_PASSWORD)
        self.today = timezone.localdate(timezone=MANILA)

        if options["reset"]:
            self._reset()
        elif User.objects.filter(email__in=all_demo_emails()).exists():
            self.stdout.write("Demo data already present — nothing to do. Use --reset to rebuild it.")
            return

        # FNRI foods + system settings the meal plans and invoices rely on.
        call_command("seed", stdout=self.stdout)

        with transaction.atomic():
            self.rnds = {p["key"]: self._create_rnd(p) for p in RNDS}
            self.clients = {p["key"]: self._create_client(p) for p in CLIENTS}
            self._benjamin()
            self._carla()
            self._daniel()
            self._elena()

        self._upload_pending_license()
        self._summary()

    # ------------------------------------------------------------------ reset
    def _reset(self):
        demo_users = User.objects.filter(email__in=all_demo_emails())
        license_ids = list(
            RndProfile.objects.filter(user__in=demo_users).exclude(prc_license_image=None)
            .values_list("prc_license_image", flat=True)
        )
        count = demo_users.count()
        demo_users.delete()  # cascades to every relationship, appointment, record, plan, invoice, message…
        for public_id in license_ids:
            self._destroy_license(public_id)
        self.stdout.write(f"Reset: deleted {count} demo accounts and all their activity.")

    def _destroy_license(self, public_id):
        try:
            import cloudinary.uploader
            from profiles.services import _configure

            _configure()
            cloudinary.uploader.destroy(public_id, type="authenticated", invalidate=True)
        except Exception as exc:  # cleanup is best-effort; never block a reset on it
            self.stderr.write(f"  (could not delete license image {public_id} from Cloudinary: {exc})")

    # ------------------------------------------------------------ accounts
    def _create_user(self, profile, role):
        return User.objects.create_user(
            email=demo_email(profile["first_name"], profile["last_name"]),
            password=self.password,
            role=role,
            first_name=profile["first_name"],
            last_name=profile["last_name"],
            phone="09" + "".join(secrets.choice("0123456789") for _ in range(9)),
            email_verified_at=timezone.now(),
        )

    def _create_rnd(self, p):
        user = self._create_user(p, User.Role.RND)
        RndProfile.objects.create(
            user=user,
            prc_license_number=p["prc"],
            specialization=p["specialization"],
            language_codes=p["languages"],
            bio=p["bio"],
            consultation_fee=p["fee"],
            consultation_modes=p["modes"],
            available_for_new_clients=p["accepting"],
            is_verified=p["verified"],
            verified_at=timezone.now() if p["verified"] else None,
        )
        for code in p["languages"]:
            RndLanguage.objects.create(rnd=user, language_code=code, language_name=LANGUAGE_NAMES[code])
        for day, start, end in p["availability"]:
            RndAvailabilitySchedule.objects.create(
                rnd=user, day_of_week=day, start_time=start, end_time=end,
                effective_from=self.today - timedelta(days=60),
            )
        user.demo_days = {day for day, _, _ in p["availability"]}
        return user

    def _create_client(self, p):
        user = self._create_user(p, User.Role.CLIENT)
        ClientProfile.objects.create(user=user, date_of_birth=p["dob"], sex=p["sex"], language_code="fil")
        ClientHealthProfile.objects.create(
            user=user,
            medical_conditions=p["conditions"],
            allergies=p.get("allergies", []),
            dietary_restrictions=p.get("restrictions", []),
            health_goals=p["goals"],
        )
        return user

    # ------------------------------------------------------------ building blocks
    def _screening(self, client, height, weight, activity, age=None, symptoms=None, chronic=False, days_ago=0):
        height, weight = Decimal(height), Decimal(weight)
        profile = client.client_profile
        if age is None and profile.date_of_birth:
            dob = profile.date_of_birth
            age = self.today.year - dob.year - ((self.today.month, self.today.day) < (dob.month, dob.day))
        bmi = calculate_bmi(weight, height)
        bmr = calculate_bmr_mifflin_st_jeor(weight, height, age, profile.sex)
        nrs_score, nrs_risk = calculate_nrs2002(bmi=bmi, severity_of_disease_points=1 if chronic else 0)
        screening = PreConsultationScreening.objects.create(
            client=client, height_cm=height, weight_kg=weight, bmi=bmi,
            bmi_category=classify_bmi_asia_pacific(bmi), bmr_kcal=bmr,
            tdee_kcal=calculate_tdee(bmr, activity), activity_level=activity,
            nrs_score=nrs_score, nrs_risk=nrs_risk, symptoms=symptoms,
        )
        PreConsultationScreening.objects.filter(pk=screening.pk).update(
            created_at=at(self.today - timedelta(days=days_ago), time(8))
        )
        return screening

    def _relationship(self, rnd, client, status, started_days_ago=None):
        rel = RndClientRelationship.objects.create(
            rnd=rnd, client=client, status=status,
            started_at=at(self.today - timedelta(days=started_days_ago), time(10)) if started_days_ago is not None else None,
        )
        return rel

    def _appointment(self, rel, when, status, kind="video", notes=None):
        appt = Appointment.objects.create(
            relationship=rel, scheduled_at=when, type=kind, status=status,
            duration_minutes=60, notes=notes,
        )
        if kind == "video" and status in (Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED):
            room = JitsiVideoService().create_room(appt)
            ended = status == Appointment.Status.COMPLETED
            ConsultationSession.objects.create(
                appointment=appt,
                video_provider=ConsultationSession.VideoProvider.JITSI,
                external_session_id=room["external_session_id"],
                host_url=room["host_url"],
                participant_url=room["participant_url"],
                session_status=ConsultationSession.SessionStatus.ENDED if ended else ConsultationSession.SessionStatus.SCHEDULED,
                session_started_at=when if ended else None,
                session_ended_at=when + timedelta(minutes=50) if ended else None,
                actual_duration_min=50 if ended else None,
            )
            appt.video_session_url = room["participant_url"]
            appt.meeting_id = room["external_session_id"]
            appt.save(update_fields=["video_session_url", "meeting_id"])
        Appointment.objects.filter(pk=appt.pk).update(created_at=when - timedelta(days=3))
        return appt

    def _invoice(self, appt, paid_method=None):
        """Same amount/commission rules as RndAppointmentCompleteView; a paid
        invoice goes through record_successful_payment like a real payment."""
        fee = appt.relationship.rnd.rnd_profile.consultation_fee
        kwargs = {"relationship": appt.relationship, "appointment": appt, "amount": fee}
        setting = SystemSetting.objects.filter(key="platform_commission_pct").first()
        if setting and setting.value:
            kwargs["commission_pct"] = Decimal(setting.value)
        invoice = Invoice.objects.create(**kwargs)
        completed_at = appt.scheduled_at + timedelta(hours=1)
        Invoice.objects.filter(pk=invoice.pk).update(created_at=completed_at)
        if paid_method:
            reference = f"demo-{secrets.token_hex(4)}"
            record_successful_payment(invoice, reference, {"source": "seed_demo"}, source="seed_demo")
            Invoice.objects.filter(pk=invoice.pk).update(
                payment_gateway=Invoice.PaymentGateway.PAYMONGO, payment_method=paid_method,
                gateway_reference_id=reference, paid_at=completed_at + timedelta(hours=2),
            )
        else:
            notify(
                recipient=appt.relationship.client, notifiable_type="invoice", notifiable_id=invoice.id,
                subject="Invoice ready", content=f"INV-{invoice.id:04d} for ₱{invoice.amount:.2f} is ready for payment.",
            )
        return invoice

    def _meal_plan(self, rel, name, condition, targets, week_menu, times, notes, restrictions, sent_days_ago):
        """week_menu: {slot: [menu for day 0, menu for day 1, …]} rotated over
        the 7 days; each menu is a list of (FNRI item name, exchanges). Food
        kcal/macros = the item's FNRI category values × exchanges, the same
        way the Meal Planning page fills them in."""
        kcal, protein, carb, fat = targets
        plan = MealPlan.objects.create(
            relationship=rel, name=name, condition=condition,
            target_kcal=Decimal(kcal), target_protein_g=Decimal(protein),
            target_carb_g=Decimal(carb), target_fat_g=Decimal(fat),
            notes=notes, allergies_restrictions=restrictions,
            status=MealPlan.Status.ACTIVE, sent_at=at(self.today - timedelta(days=sent_days_ago), time(16)),
        )
        items = {i.name: i for i in FoodExchangeItem.objects.select_related("category")}
        for day in range(7):
            for slot, menus in week_menu.items():
                meal = MealPlanMeal.objects.create(
                    meal_plan=plan, day_of_week=day, meal_time=slot, scheduled_time=times[slot],
                )
                for food_name, exchanges in menus[day % len(menus)]:
                    item = items[food_name]
                    cat, ex = item.category, Decimal(str(exchanges))
                    MealPlanFoodItem.objects.create(
                        meal_plan_meal=meal, food_item=item, food_name=item.name,
                        source_type=MealPlanFoodItem.SourceType.FEL, exchanges=ex,
                        household_measure=item.household_measure,
                        kcal=cat.kcal_per_exchange * ex, carbs_g=(cat.carbs_g or 0) * ex,
                        protein_g=(cat.protein_g or 0) * ex, fat_g=(cat.fat_g or 0) * ex,
                    )
                meal.recompute_exchanges()
        notify(
            recipient=rel.client, notifiable_type="meal_plan", notifiable_id=plan.id,
            subject="New meal plan", content=f"{rel.rnd.full_name} sent you a new meal plan: {plan.name}.",
        )
        return plan

    def _messages(self, rel, lines, days_ago):
        start = at(self.today - timedelta(days=days_ago), time(9))
        for i, (sender_is_rnd, text) in enumerate(lines):
            msg = Message.objects.create(
                relationship=rel, sender=rel.rnd if sender_is_rnd else rel.client,
                message=text, is_read=True, read_at=start + timedelta(minutes=30 * i + 5),
            )
            Message.objects.filter(pk=msg.pk).update(created_at=start + timedelta(minutes=30 * i))

    # ------------------------------------------------------------ clients
    def _benjamin(self):
        """Screened, not with any RND yet — ready to find and book one.
        Values match TESTING_PLAN.md flow B: male, 172 cm, 90 kg, 31 y (as of
        2026), lightly active → BMI 30.42 (Obese II), BMR 1825, TDEE 2509.38."""
        self._screening(self.clients["benjamin"], "172", "90", "lightly_active",
                        symptoms="Elevated blood glucose", days_ago=2)

    def _carla(self):
        """Maria's active patient with a full history: 2 completed visits
        (one paid + reviewed, one invoice still unpaid), finalized NCP +
        a follow-up draft, weekly meal plan with meal logs, 4 progress
        records, messages, and an upcoming confirmed video visit."""
        carla, maria = self.clients["carla"], self.rnds["maria"]
        screening = self._screening(carla, "157", "78", "lightly_active",
                                    symptoms="Elevated blood glucose", chronic=True, days_ago=31)
        rel = self._relationship(maria, carla, RndClientRelationship.Status.ACTIVE, started_days_ago=28)

        first_day = shift_to_day(self.today - timedelta(days=28), maria.demo_days, -1)
        first = self._appointment(rel, at(first_day, time(10)), Appointment.Status.COMPLETED,
                                  notes="Newly diagnosed with type 2 diabetes, want help with meal planning.")
        followup_day = shift_to_day(self.today - timedelta(days=7), maria.demo_days, -1)
        followup = self._appointment(rel, at(followup_day, time(10)), Appointment.Status.COMPLETED)
        upcoming_day = shift_to_day(self.today + timedelta(days=5), maria.demo_days, 1)
        self._appointment(rel, at(upcoming_day, time(14)), Appointment.Status.CONFIRMED)

        self._invoice(first, paid_method=Invoice.PaymentMethod.GCASH)
        self._invoice(followup)  # left unpaid so the Pay Now flow can be demoed
        Review.objects.create(
            appointment=first, client=carla, rnd=maria, rating=5,
            comment="Very clear explanations and a meal plan I can actually follow with Filipino food.",
        )

        height = screening.height_cm
        NcpRecord.objects.create(
            relationship=rel, appointment=first, encounter_date=first_day, status=NcpRecord.Status.COMPLETED,
            weight_kg=Decimal("78"), height_cm=height, bmi=calculate_bmi(Decimal("78"), height),
            blood_pressure="130/85", blood_glucose=Decimal("148"), hba1c=Decimal("7.9"),
            lab_notes="FBS 148 mg/dL, HbA1c 7.9% (lab dated one week before visit).",
            assessment_notes="Newly diagnosed T2DM. About 4 cups of rice a day and sweetened drinks with meals; sedentary office job.",
            assessment_extra=[
                {"label": "Waist circumference", "value": "94", "unit": "cm"},
                {"label": "Triglycerides", "value": "195", "unit": "mg/dL"},
            ],
            pes_problem="Excessive carbohydrate intake",
            pes_etiology="frequent large servings of white rice and sweetened beverages",
            pes_signs="FBS 148 mg/dL, HbA1c 7.9%, diet recall of 4 cups rice/day",
            diet_prescription="1500 kcal low-GI Filipino diet. Brown rice, 1 cup max per meal; water instead of sweetened drinks.",
            target_kcal=Decimal("1500"), target_protein_g=Decimal("75"), target_carb_g=Decimal("188"), target_fat_g=Decimal("50"),
            intervention_notes="Taught carb counting with the FNRI exchange lists.",
            intervention_extra=[
                {"label": "Physical activity", "value": "30 brisk walking", "unit": "min/day"},
                {"label": "Nutrition education topic", "value": "Carb counting with FNRI exchange lists", "unit": ""},
            ],
            monitoring_notes="Baseline visit. Monitor FBS weekly and weight at next visit.",
            goal_status=NcpRecord.GoalStatus.ONGOING,
        )
        NcpRecord.objects.create(
            relationship=rel, appointment=followup, encounter_date=followup_day, status=NcpRecord.Status.DRAFT,
            weight_kg=Decimal("76.5"), height_cm=height, bmi=calculate_bmi(Decimal("76.5"), height),
            blood_pressure="126/82", blood_glucose=Decimal("132"),
            assessment_notes="Down 1.5 kg. Switched to brown rice most days; still has soft drinks on weekends.",
            pes_problem="Excessive carbohydrate intake",
            pes_etiology="weekend sweetened beverage intake",
            pes_signs="FBS improved to 132 mg/dL; weekend diet recall",
        )

        breakfast = [
            [("Egg, whole, chicken", 1), ("Rice, undermilled/brown rice, boiled", 1), ("Papaya, ripe", 1)],
            [("Bread, pan de sal", 1), ("Cheese, cheddar, pasteurized, processed", 1), ("Milk, skim", 1)],
            [("Sweet potato (yellow, purple, white)", 1), ("Tofu (Soy bean curd)", 1), ("Saging, lakatan (Banana, lacatan)", 1)],
        ]
        lunch = [
            [("Rice, undermilled/brown rice, boiled", 2), ("Bangus (Milkfish)", 2), ("Kangkong (Swamp cabbage), leaves", 1), ("Oil (canola, corn, soybean, sunflower)", 1)],
            [("Rice, undermilled/brown rice, boiled", 2), ("Chicken breast/white meat, no skin", 2), ("Pechay (Pechay), leaves", 1), ("Oil (canola, corn, soybean, sunflower)", 1)],
            [("Rice, undermilled/brown rice, boiled", 2), ("Tilapia", 2), ("Sitaw (String/yard long bean), pod", 1), ("Oil (canola, corn, soybean, sunflower)", 1)],
        ]
        snack = [[("Mansanas, red (Apple, red)", 1)], [("Suha (Pomelo)", 1)], [("Yogurt, plain, skim", 1)]]
        dinner = [
            [("Rice, undermilled/brown rice, boiled", 1.5), ("Chicken breast/white meat, no skin", 2), ("Ampalaya (Bittermelon/gourd), leaves", 1), ("Talong (Eggplant)", 1)],
            [("Rice, undermilled/brown rice, boiled", 1.5), ("Tuna, yellow-fin", 2), ("Malunggay (Horseradish tree), leaves", 1), ("Kalabasa (Squash), fruit", 1)],
            [("Rice, undermilled/brown rice, boiled", 1.5), ("Mongo (Munggo), seeds, dried", 1), ("Malunggay (Horseradish tree), leaves", 1), ("Broccoli", 1)],
        ]
        plan = self._meal_plan(
            rel, "Diabetic-Friendly Plan", MealPlan.Condition.DIABETES, (1500, 75, 188, 50),
            {"breakfast": breakfast, "lunch": lunch, "pm_snack": snack, "dinner": dinner},
            {"breakfast": time(7), "lunch": time(12), "pm_snack": time(15, 30), "dinner": time(18, 30)},
            notes="Eat at regular times and don't skip meals. Water instead of sweetened drinks.",
            restrictions="Shrimp allergy. Limit rice to 1 cup per meal; no sweetened drinks.",
            sent_days_ago=27,
        )

        # Meal logs for the last 4 days (not today, so there's something left to log in the demo).
        statuses = ["followed", "followed", "partially_followed", "followed", "not_followed", "followed", "followed"]
        n = 0
        for back in range(4, 0, -1):
            day = self.today - timedelta(days=back)
            for meal in plan.meals.filter(day_of_week=dow(day)).order_by("scheduled_time"):
                status = statuses[n % len(statuses)]
                n += 1
                MealLog.objects.create(
                    meal_plan_meal=meal, client=carla, log_date=day, status=status,
                    time_logged=(datetime.combine(day, meal.scheduled_time) + timedelta(minutes=15)).time(),
                    reason_notes={"partially_followed": "Only had half a cup of rice left.",
                                  "not_followed": "Ate out at a family party."}.get(status),
                )

        for back, weight, glucose, bp, adherence, note in [
            (21, "77.6", "145", "130/84", 70, "Started brown rice; adjusting to smaller portions."),
            (14, "77.0", "138", "128/84", 78, "Walking 20 minutes after dinner most days."),
            (7, "76.5", "132", "126/82", 82, "Good week. Weekend soft drinks still an issue."),
            (1, "75.9", "126", "124/80", 85, "Keep going — on track for the 3-month goal."),
        ]:
            ProgressRecord.objects.create(
                relationship=rel, record_date=self.today - timedelta(days=back),
                weight_kg=Decimal(weight), bmi=calculate_bmi(Decimal(weight), height),
                blood_pressure=bp, blood_glucose=Decimal(glucose), adherence_pct=adherence, rnd_notes=note,
            )

        self._messages(rel, [
            (False, "Good morning po! Is it okay to eat pan de sal instead of rice for breakfast?"),
            (True, "Good morning Carla! Yes, 1½ pieces of pan de sal is one rice exchange, so you can swap them."),
            (False, "Thank you! My FBS this morning was 126."),
            (True, "That's a big improvement from 148. Keep logging your meals and we'll review everything at your next visit."),
        ], days_ago=2)

    def _daniel(self):
        """Jose's active patient with a lighter history: one completed,
        paid and reviewed video visit, a finalized NCP and a
        low-sodium meal plan."""
        daniel, jose = self.clients["daniel"], self.rnds["jose"]
        screening = self._screening(daniel, "168", "82", "sedentary",
                                    symptoms="Recent hospitalization", chronic=True, days_ago=14)
        rel = self._relationship(jose, daniel, RndClientRelationship.Status.ACTIVE, started_days_ago=10)
        visit_day = shift_to_day(self.today - timedelta(days=10), jose.demo_days, -1)
        visit = self._appointment(rel, at(visit_day, time(14)), Appointment.Status.COMPLETED,
                                  notes="Doctor advised a low-salt diet after a hypertension admission.")
        self._invoice(visit, paid_method=Invoice.PaymentMethod.MAYA)
        Review.objects.create(appointment=visit, client=daniel, rnd=jose, rating=4,
                              comment="Practical tips for cutting salt from Filipino dishes.")

        height = screening.height_cm
        NcpRecord.objects.create(
            relationship=rel, appointment=visit, encounter_date=visit_day, status=NcpRecord.Status.COMPLETED,
            weight_kg=Decimal("82"), height_cm=height, bmi=calculate_bmi(Decimal("82"), height),
            blood_pressure="150/95", blood_glucose=Decimal("98"),
            assessment_notes="Hypertension, recently hospitalized. Frequent patis, toyo and instant noodles.",
            assessment_extra=[{"label": "Serum sodium", "value": "144", "unit": "mmol/L"}],
            pes_problem="Excessive sodium intake",
            pes_etiology="frequent use of patis, toyo and processed foods",
            pes_signs="BP 150/95 mmHg, diet recall high in condiments and instant noodles",
            diet_prescription="1800 kcal DASH-style diet, sodium under 2,000 mg/day. No instant noodles or processed meats.",
            target_kcal=Decimal("1800"), target_protein_g=Decimal("80"), target_carb_g=Decimal("250"), target_fat_g=Decimal("50"),
            intervention_extra=[{"label": "Sodium limit", "value": "2000", "unit": "mg/day"}],
            monitoring_notes="Check BP at home daily; review in 4 weeks.",
            goal_status=NcpRecord.GoalStatus.ONGOING,
        )
        self._meal_plan(
            rel, "Low-Sodium DASH Plan", MealPlan.Condition.HYPERTENSION, (1800, 80, 250, 50),
            {
                "breakfast": [[("Rice, well-milled, boiled", 2), ("Egg, whole, chicken", 1), ("Saging, lakatan (Banana, lacatan)", 1)],
                              [("Bread, white, loaf", 1), ("Milk, low fat", 1), ("Papaya, ripe", 1)]],
                "lunch": [[("Rice, well-milled, boiled", 2), ("Tilapia", 2), ("Pechay (Pechay), leaves", 1), ("Oil (canola, corn, soybean, sunflower)", 1)],
                          [("Rice, well-milled, boiled", 2), ("Chicken breast/white meat, no skin", 2), ("Sitaw (String/yard long bean), pod", 1), ("Oil (canola, corn, soybean, sunflower)", 1)]],
                "dinner": [[("Rice, well-milled, boiled", 2), ("Bangus (Milkfish)", 2), ("Kalabasa (Squash), fruit", 1)],
                           [("Rice, well-milled, boiled", 2), ("Tofu (Soy bean curd)", 2), ("Toge (Mung bean sprout)", 1)]],
            },
            {"breakfast": time(7), "lunch": time(12), "dinner": time(19)},
            notes="Cook without patis or toyo — use calamansi, garlic and ginger for flavor.",
            restrictions="Low sodium: under 2,000 mg/day.",
            sent_days_ago=9,
        )
        self._messages(rel, [
            (False, "Doc, pwede pa ba ang sinigang?"),
            (True, "Yes, just use fresh sampalok or calamansi instead of the powdered mix — the mix is very high in sodium."),
        ], days_ago=5)

    def _elena(self):
        """Screened and has just booked Ramon — a first booking, so the
        relationship and appointment are both still pending, waiting for
        Ramon to confirm."""
        elena, ramon = self.clients["elena"], self.rnds["ramon"]
        self._screening(elena, "160", "58", "moderately_active", days_ago=1)
        rel = self._relationship(ramon, elena, RndClientRelationship.Status.PENDING)
        day = shift_to_day(self.today + timedelta(days=3), ramon.demo_days, 1)
        appt = self._appointment(rel, at(day, time(11)), Appointment.Status.PENDING, kind="in_person",
                                 notes="Would like help planning healthier meals for my two kids.")
        notify(recipient=ramon, notifiable_type="appointment", notifiable_id=appt.id,
               subject="New booking", content="Elena Ramos booked an in-person consultation.")

    # ------------------------------------------------------------ extras
    def _upload_pending_license(self):
        """Kristine is pending admin review, so she needs a license photo to
        review. Uploaded after the DB transaction (network call); skipped
        with a warning if Cloudinary isn't configured."""
        profile = self.rnds["kristine"].rnd_profile
        try:
            from profiles.services import upload_prc_license_image

            profile.prc_license_image = upload_prc_license_image(placeholder_license_png())
            profile.save(update_fields=["prc_license_image"])
        except Exception as exc:
            self.stderr.write(f"  (license photo for the pending RND not uploaded: {exc})")

    def _summary(self):
        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write(f"All demo accounts use the password from DEMO_PASSWORD (default: {DEFAULT_DEMO_PASSWORD}).")
        for p in RNDS:
            state = "pending verification" if not p["verified"] else ("not accepting new clients" if not p["accepting"] else "verified")
            self.stdout.write(f"  RND     {demo_email(p['first_name'], p['last_name']):38} {p['specialization']} — {state}")
        notes = {
            "ana": "brand new, no screening",
            "benjamin": "screened, no RND yet",
            "carla": "Maria's patient — full history, 1 unpaid invoice, upcoming visit",
            "daniel": "Jose's patient — 1 paid visit, meal plan",
            "elena": "first booking with Ramon, waiting for confirmation",
        }
        for p in CLIENTS:
            self.stdout.write(f"  Client  {demo_email(p['first_name'], p['last_name']):38} {notes[p['key']]}")
