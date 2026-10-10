"""Automated reminders (proposal: "automated reminder module delivering
notifications for appointments, meal logging, and motivational prompts").

`run_due_reminders()` is the ReminderScheduler: the `send_reminders`
management command runs it on a schedule, and it also runs (throttled)
whenever a client opens the app, so reminders arrive even on a laptop with
no scheduler set up. Each reminder becomes an in-app notification, plus an
email when the client turned email on (off by default).
"""

import logging
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

MEAL_WINDOW = timedelta(hours=2)    # remind during the 2 hours after a planned meal time
STALE_AFTER = timedelta(days=1)     # an RND reminder this overdue is skipped, not sent late


def ph_tz():
    from scheduling.serializers import PH_TZ

    return PH_TZ


def _clock(dt):
    local = dt.astimezone(ph_tz())
    return f"{local.hour % 12 or 12}:{local:%M} {local:%p}"


def _when(dt):
    from scheduling.views import format_ph_datetime

    return format_ph_datetime(dt)


# ------------------------------------------------------------- recurrence
def next_occurrence(reminder, after):
    """Next time `reminder` fires strictly after `after` (aware), keeping its
    Philippine time of day; None for a one-off."""
    if reminder.repeat == reminder.Repeat.ONCE:
        return None
    ph = ph_tz()
    base = reminder.send_at.astimezone(ph)
    t = base.timetz().replace(tzinfo=None)
    day = after.astimezone(ph).date()
    for offset in range(0, 15):
        d = day + timedelta(days=offset)
        candidate = datetime.combine(d, t, tzinfo=ph)
        if candidate <= after:
            continue
        if reminder.repeat == reminder.Repeat.WEEKDAYS and d.weekday() >= 5:
            continue
        if reminder.repeat == reminder.Repeat.WEEKLY and d.weekday() != base.weekday():
            continue
        return candidate
    return None


def first_occurrence(repeat, start):
    """Weekday reminders that start on a weekend move to Monday."""
    from .models import Reminder

    if repeat == Reminder.Repeat.WEEKDAYS:
        ph = ph_tz()
        local = start.astimezone(ph)
        while local.weekday() >= 5:
            local += timedelta(days=1)
        return local
    return start


# ------------------------------------------------------------- delivery
def _deliver(client, pref, *, subject, content, notifiable_type, notifiable_id, link, link_label):
    from .services import notify

    notify(recipient=client, notifiable_type=notifiable_type, notifiable_id=notifiable_id, subject=subject, content=content)
    if pref.email:
        try:
            from accounts.emails import send_notice_email

            send_notice_email(
                client, subject=f"Reminder: {subject}", heading=subject, paragraphs=[content],
                button_label=link_label, button_url=f"{settings.FRONTEND_URL}{link}",
                preheader=content[:120],
            )
        except Exception:
            logger.exception("Could not email reminder %r to %s", subject, client.pk)


def _claim(key, **fields):
    """Record an automatic reminder once; None if it was already sent."""
    from .models import Reminder

    try:
        with transaction.atomic():
            return Reminder.objects.create(source_key=key, is_sent=True, last_sent_at=timezone.now(), **fields)
    except IntegrityError:
        return None


# ------------------------------------------------------------- the scheduler
def run_due_reminders(now=None, client=None):
    """Send every reminder that's due. `client` limits it to one person (the
    on-open run). Returns how many were sent."""
    from billing.models import Invoice
    from nutrition.models import MealLog, MealPlan, MealPlanMeal
    from scheduling.models import Appointment, RndClientRelationship

    from .models import Reminder, ReminderPreference

    now = now or timezone.now()
    ph = ph_tz()
    prefs = {}

    def pref_for(user):
        if user.pk not in prefs:
            prefs[user.pk] = ReminderPreference.for_user(user)
        return prefs[user.pk]

    sent = 0
    scope = {"relationship__client": client} if client else {}

    # 1) consultations: 24 hours and 1 hour before
    appts = (Appointment.objects.filter(status="confirmed", scheduled_at__gt=now, scheduled_at__lte=now + timedelta(hours=24), **scope)
             .select_related("relationship__client", "relationship__rnd"))
    for appt in appts:
        c, rnd = appt.relationship.client, appt.relationship.rnd
        if not pref_for(c).appointments:
            continue
        soon = appt.scheduled_at - now <= timedelta(hours=1)
        key = f"appt:{appt.id}:{'1h' if soon else '24h'}"
        kind = appt.get_type_display().lower()
        # "today" / "tomorrow" by the Philippine calendar date, not by hours left
        days = (appt.scheduled_at.astimezone(ph).date() - now.astimezone(ph).date()).days
        day_word = "today" if days == 0 else "tomorrow"
        content = (f"Your {kind} consultation with RND {rnd.full_name} is {day_word} at {_clock(appt.scheduled_at)}. "
                   "You can join from My Appointments 15 minutes before it starts.")
        subject = "Your consultation starts soon" if soon else f"Consultation {day_word}"
        if _claim(key, client=c, title=subject, message=content, type=Reminder.Type.APPOINTMENT, send_at=now):
            _deliver(c, pref_for(c), subject=subject, content=content, notifiable_type="appointment",
                     notifiable_id=appt.id, link="/appointments", link_label="Open My Appointments")
            sent += 1

    # 2) payment still due within 24 hours of the start
    invoices = (Invoice.objects.filter(status=Invoice.Status.UNPAID, appointment__status="confirmed",
                                       appointment__scheduled_at__gt=now, appointment__scheduled_at__lte=now + timedelta(hours=24),
                                       **({"relationship__client": client} if client else {}))
                .select_related("relationship__client", "appointment"))
    for inv in invoices:
        c = inv.relationship.client
        if not pref_for(c).payments:
            continue
        content = (f"Please pay ₱{inv.amount:,.2f} (INV-{inv.id:04d}) before {_when(inv.appointment.scheduled_at)}. "
                   "Unpaid consultations are cancelled automatically at the start time.")
        if _claim(f"pay:{inv.id}", client=c, title="Payment due", message=content, type=Reminder.Type.PAYMENT, send_at=now):
            _deliver(c, pref_for(c), subject="Payment due before your consultation", content=content,
                     notifiable_type="invoice", notifiable_id=inv.id, link="/invoices-billing", link_label="Pay now")
            sent += 1

    # 3) meal logging: during the 2 hours after each planned meal time, if not logged
    local_now = now.astimezone(ph)
    today = local_now.date()
    dow = (today.weekday() + 1) % 7  # Sunday=0
    meals = (MealPlanMeal.objects.filter(meal_plan__status=MealPlan.Status.ACTIVE, meal_plan__relationship__status=RndClientRelationship.Status.ACTIVE,
                                         scheduled_time__isnull=False)
             .filter(Q(day_of_week=dow) | Q(day_of_week__isnull=True))
             .select_related("meal_plan__relationship__client"))
    if client:
        meals = meals.filter(meal_plan__relationship__client=client)
    logged = set(MealLog.objects.filter(log_date=today, meal_plan_meal__in=meals).values_list("meal_plan_meal_id", flat=True))
    for meal in meals:
        at = datetime.combine(today, meal.scheduled_time, tzinfo=ph)
        if not (at <= now < at + MEAL_WINDOW) or meal.id in logged:
            continue
        c = meal.meal_plan.relationship.client
        if not pref_for(c).meal_logging:
            continue
        label = meal.get_meal_time_display()
        content = f"Time for {label.lower()}! Log what you ate so your RND can follow your progress."
        if _claim(f"meal:{meal.id}:{today.isoformat()}", client=c, title=f"Log your {label.lower()}", message=content,
                  type=Reminder.Type.MEAL_LOG, send_at=at):
            _deliver(c, pref_for(c), subject=f"Log your {label.lower()}", content=content, notifiable_type="meal_plan",
                     notifiable_id=meal.meal_plan_id, link="/meal-plan-view", link_label="Log my meal")
            sent += 1

    # 4) reminders the RND set (medication cues, habit prompts)
    due = (Reminder.objects.filter(created_by__isnull=False, is_active=True, is_sent=False, send_at__lte=now,
                                   relationship__status=RndClientRelationship.Status.ACTIVE)
           .select_related("client", "created_by"))
    if client:
        due = due.filter(client=client)
    for r in due:
        with transaction.atomic():
            r = Reminder.objects.select_for_update().get(pk=r.pk)
            if r.is_sent or r.send_at > now:
                continue  # another run got it first
            c = r.client
            fresh = now - r.send_at <= STALE_AFTER
            if fresh and not r.is_muted and pref_for(c).rnd_reminders:
                content = r.message or f"A reminder from RND {r.created_by.full_name}."
                _deliver(c, pref_for(c), subject=r.title, content=content, notifiable_type="reminder",
                         notifiable_id=r.id, link="/profile-settings?tab=notifications", link_label="See my reminders")
                r.last_sent_at = now
                sent += 1
            nxt = next_occurrence(r, now)
            if nxt is None:
                r.is_sent = True
            else:
                r.send_at = nxt
            r.save(update_fields=["is_sent", "send_at", "last_sent_at"])
    return sent


def run_for_client_throttled(client, seconds=60):
    """The on-open run, at most once a minute per client."""
    from django.core.cache import cache

    if cache.add(f"reminders-run:{client.pk}", 1, seconds):
        try:
            run_due_reminders(client=client)
        except Exception:
            logger.exception("Reminder run failed for client %s", client.pk)


# ------------------------------------------------------------- "coming up today"
def today_items(client, now=None):
    """What's on today for the client dashboard: consultations, planned meals
    (logged or not) and RND reminders, in time order (Philippine time)."""
    from nutrition.models import MealLog, MealPlan, MealPlanMeal
    from scheduling.models import Appointment

    from .models import Reminder

    now = now or timezone.now()
    ph = ph_tz()
    today = now.astimezone(ph).date()
    start = datetime.combine(today, time.min, tzinfo=ph)
    end = start + timedelta(days=1)
    items = []

    for a in (Appointment.objects.filter(relationship__client=client, status__in=["pending", "confirmed"],
                                         scheduled_at__gte=start, scheduled_at__lt=end)
              .select_related("relationship__rnd")):
        items.append({"kind": "appointment", "at": a.scheduled_at, "title": f"Consultation with RND {a.relationship.rnd.full_name}",
                      "detail": a.get_type_display() + (" · waiting for confirmation" if a.status == "pending" else ""),
                      "done": False, "link": "/appointments"})

    dow = (today.weekday() + 1) % 7
    meals = (MealPlanMeal.objects.filter(meal_plan__relationship__client=client, meal_plan__status=MealPlan.Status.ACTIVE,
                                         scheduled_time__isnull=False)
             .filter(Q(day_of_week=dow) | Q(day_of_week__isnull=True)))
    logged = set(MealLog.objects.filter(log_date=today, meal_plan_meal__in=meals).values_list("meal_plan_meal_id", flat=True))
    for m in meals:
        items.append({"kind": "meal", "at": datetime.combine(today, m.scheduled_time, tzinfo=ph),
                      "title": f"Log your {m.get_meal_time_display().lower()}", "detail": "Logged" if m.id in logged else "",
                      "done": m.id in logged, "link": "/meal-plan-view"})

    for r in Reminder.objects.filter(client=client, created_by__isnull=False, is_active=True, is_muted=False, is_sent=False,
                                     send_at__gte=start, send_at__lt=end).select_related("created_by"):
        items.append({"kind": "reminder", "at": r.send_at, "title": r.title, "detail": f"From RND {r.created_by.full_name}",
                      "done": False, "link": "/profile-settings?tab=notifications"})
    for r in Reminder.objects.filter(client=client, created_by__isnull=False, last_sent_at__gte=start, last_sent_at__lt=end):
        # already sent earlier today (a repeating one has moved on to its next time)
        items.append({"kind": "reminder", "at": r.last_sent_at, "title": r.title, "detail": "Sent", "done": True,
                      "link": "/profile-settings?tab=notifications"})

    items.sort(key=lambda i: i["at"])
    return items
