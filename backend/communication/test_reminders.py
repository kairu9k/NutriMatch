"""Automated reminders: appointments, payments, meal logging, RND-set ones."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import MealLog, MealPlan, MealPlanMeal
from scheduling.models import Appointment, RndClientRelationship

from .models import NotificationLog, Reminder, ReminderPreference
from .reminders import run_due_reminders, today_items

PH = ZoneInfo("Asia/Manila")
NOW = datetime(2026, 10, 12, 8, 0, tzinfo=PH)  # Monday 8:00 AM


class ReminderTests(TestCase):
    def setUp(self):
        mail.outbox = []
        self.rnd = approve_rnd(User.objects.create_user(email="rnd@m.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.client_user = onboard_client(User.objects.create_user(email="ana@m.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

    def _notes(self, **kw):
        return list(NotificationLog.objects.filter(recipient=self.client_user, **kw).values_list("subject", flat=True))

    def _appt(self, when, status="confirmed", invoice=None):
        a = Appointment.objects.create(relationship=self.rel, type="video", status=status, scheduled_at=when, duration_minutes=60)
        if invoice:
            Invoice.objects.create(relationship=self.rel, appointment=a, amount=Decimal("800"), status=invoice)
        return a

    # -- appointments
    def test_appointment_24h_then_1h_once_each(self):
        appt = self._appt(NOW + timedelta(hours=20), invoice="paid")
        run_due_reminders(now=NOW)
        run_due_reminders(now=NOW + timedelta(minutes=5))
        self.assertEqual(self._notes(notifiable_type="appointment"), ["Consultation tomorrow"])
        run_due_reminders(now=appt.scheduled_at - timedelta(minutes=50))
        run_due_reminders(now=appt.scheduled_at - timedelta(minutes=40))
        self.assertEqual(sorted(self._notes(notifiable_type="appointment")), ["Consultation tomorrow", "Your consultation starts soon"])

    def test_same_day_says_today(self):
        self._appt(NOW + timedelta(hours=3), invoice="paid")
        run_due_reminders(now=NOW)
        n = NotificationLog.objects.get(recipient=self.client_user, notifiable_type="appointment")
        self.assertEqual(n.subject, "Consultation today")
        self.assertIn("is today at 11:00 AM", n.content)

    def test_turned_off_means_nothing(self):
        ReminderPreference.objects.create(user=self.client_user, appointments=False, payments=False)
        self._appt(NOW + timedelta(hours=3), invoice="unpaid")
        self.assertEqual(run_due_reminders(now=NOW), 0)

    def test_payment_due(self):
        self._appt(NOW + timedelta(hours=10), invoice="unpaid")
        run_due_reminders(now=NOW)
        run_due_reminders(now=NOW + timedelta(hours=1))
        self.assertEqual(self._notes(notifiable_type="invoice"), ["Payment due before your consultation"])

    # -- meals
    def _meal(self, at=time(7, 30)):
        plan = MealPlan.objects.create(relationship=self.rel, name="Plan", status="active")
        return MealPlanMeal.objects.create(meal_plan=plan, day_of_week=1, meal_time="breakfast", scheduled_time=at)  # Monday

    def test_meal_reminder_only_in_window_and_if_not_logged(self):
        meal = self._meal()
        self.assertEqual(run_due_reminders(now=NOW - timedelta(hours=1)), 0)   # 7:00, before breakfast time
        self.assertEqual(run_due_reminders(now=NOW), 1)                       # 8:00, 30 min after
        self.assertEqual(run_due_reminders(now=NOW + timedelta(minutes=10)), 0)  # never twice
        lunch = MealPlanMeal.objects.create(meal_plan=meal.meal_plan, day_of_week=1, meal_time="lunch", scheduled_time=time(12))
        MealLog.objects.create(meal_plan_meal=lunch, client=self.client_user, log_date=NOW.date(), status="followed")
        self.assertEqual(run_due_reminders(now=NOW.replace(hour=12, minute=30)), 0)  # already logged

    # -- RND reminders via the API
    def _rnd_api(self):
        api = APIClient()
        api.force_authenticate(self.rnd)
        return api

    def test_rnd_creates_daily_reminder_and_it_repeats(self):
        api = self._rnd_api()
        url = f"/api/rnd/relationships/{self.rel.id}/reminders/"
        self.assertEqual(api.post(url, {"title": "x", "type": "medication", "repeat": "daily", "date": "2026-10-12", "time": "09:00"}, format="json").status_code, 400)
        resp = api.post(url, {"title": "Take metformin", "message": "After breakfast.", "type": "medication", "repeat": "daily",
                              "date": "2030-01-01", "time": "09:00"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertIn("New reminder from your RND", self._notes(notifiable_type="reminder"))
        r = Reminder.objects.get(pk=resp.data["id"])
        Reminder.objects.filter(pk=r.pk).update(send_at=NOW - timedelta(minutes=5))
        self.assertEqual(run_due_reminders(now=NOW), 1)
        r.refresh_from_db()
        self.assertFalse(r.is_sent)
        self.assertEqual(r.send_at.astimezone(PH), datetime(2026, 10, 13, 7, 55, tzinfo=PH))  # next day, same time
        self.assertIn("Take metformin", self._notes(notifiable_type="reminder"))

    def test_muted_and_stale_are_skipped_but_move_on(self):
        r = Reminder.objects.create(client=self.client_user, relationship=self.rel, created_by=self.rnd, title="Walk",
                                    repeat="weekdays", send_at=NOW - timedelta(minutes=1), is_muted=True)
        self.assertEqual(run_due_reminders(now=NOW), 0)
        r.refresh_from_db()
        self.assertGreater(r.send_at, NOW)
        once = Reminder.objects.create(client=self.client_user, relationship=self.rel, created_by=self.rnd, title="Old",
                                       send_at=NOW - timedelta(days=3))
        self.assertEqual(run_due_reminders(now=NOW), 0)
        once.refresh_from_db()
        self.assertTrue(once.is_sent)

    def test_email_only_when_turned_on(self):
        self._appt(NOW + timedelta(hours=3), invoice="paid")
        run_due_reminders(now=NOW)
        self.assertEqual(mail.outbox, [])
        ReminderPreference.objects.filter(user=self.client_user).update(email=True)
        self._appt(NOW + timedelta(hours=5), invoice="paid")
        run_due_reminders(now=NOW)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reminder:", mail.outbox[0].subject)

    def test_client_settings_mute_and_privacy(self):
        api = APIClient()
        api.force_authenticate(self.client_user)
        self.assertFalse(api.get("/api/client/reminder-settings/").data["email"])  # off by default
        self.assertTrue(api.put("/api/client/reminder-settings/", {"email": True}, format="json").data["email"])
        r = Reminder.objects.create(client=self.client_user, relationship=self.rel, created_by=self.rnd, title="Water",
                                    repeat="daily", send_at=NOW + timedelta(days=400))
        self.assertEqual([x["title"] for x in api.get("/api/client/reminders/").data], ["Water"])
        self.assertTrue(api.patch(f"/api/client/reminders/{r.id}/", {"is_muted": True}, format="json").data["is_muted"])
        # another RND can't touch it; another client can't see it
        other = approve_rnd(User.objects.create_user(email="o@m.ph", password="x", role="rnd", first_name="O", last_name="R"))
        oapi = APIClient()
        oapi.force_authenticate(other)
        self.assertEqual(oapi.patch(f"/api/rnd/reminders/{r.id}/", {"title": "Hacked"}, format="json").status_code, 404)
        self.assertEqual(oapi.get(f"/api/rnd/relationships/{self.rel.id}/reminders/").status_code, 404)

    def test_today_items(self):
        self._meal(at=time(7, 30))
        self._appt(NOW + timedelta(hours=6))
        Reminder.objects.create(client=self.client_user, relationship=self.rel, created_by=self.rnd, title="Water",
                                send_at=NOW + timedelta(hours=2))
        kinds = [i["kind"] for i in today_items(self.client_user, now=NOW)]
        self.assertEqual(kinds, ["meal", "task", "appointment"])

    def test_my_tasks_checkbox_and_own_tasks(self):
        from rest_framework.test import APIClient

        rnd_task = Reminder.objects.create(client=self.client_user, relationship=self.rel, created_by=self.rnd, title="Water",
                                           send_at=timezone.now() + timedelta(minutes=30), repeat="daily")
        api = APIClient()
        api.force_authenticate(self.client_user)
        # The client adds their own task.
        local = (timezone.now() + timedelta(minutes=20)).astimezone(ZoneInfo("Asia/Manila"))
        own = api.post("/api/client/reminders/", {"title": "Walk 20 minutes", "date": local.date().isoformat(),
                                                  "time": local.strftime("%H:%M"), "repeat": "daily"}, format="json")
        self.assertEqual(own.status_code, 201, own.data)
        tasks = [i for i in api.get("/api/client/today/").data if i["kind"] == "task"]
        self.assertEqual({t["title"]: t["own"] for t in tasks}, {"Water": False, "Walk 20 minutes": True})
        self.assertFalse(any(t["done"] for t in tasks))
        # Tick the RND's task off; it shows as done today, also on the RND's side.
        self.assertTrue(api.post(f"/api/client/reminders/{rnd_task.id}/check/", {"done": True}, format="json").data["done"])
        tasks = {t["title"]: t["done"] for t in api.get("/api/client/today/").data if t["kind"] == "task"}
        self.assertEqual(tasks, {"Water": True, "Walk 20 minutes": False})
        rnd_api = APIClient()
        rnd_api.force_authenticate(self.rnd)
        self.assertTrue(rnd_api.get(f"/api/rnd/relationships/{self.rel.id}/reminders/").data[0]["done_today"])
        # Clients can delete only their own tasks.
        self.assertEqual(api.delete(f"/api/client/reminders/{rnd_task.id}/").status_code, 404)
        self.assertEqual(api.delete(f"/api/client/reminders/{own.data['id']}/").status_code, 204)
