"""SMS reminders through Semaphore — the HTTP call is mocked; no real texts."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import MealPlan, MealPlanMeal
from scheduling.models import Appointment, RndClientRelationship

from .models import Reminder, ReminderPreference
from .reminders import run_due_reminders
from .sms import fit_message, mask_mobile, normalize_ph_mobile, send_sms

PH = ZoneInfo("Asia/Manila")
NOW = datetime(2026, 10, 12, 8, 0, tzinfo=PH)


def _ok_response():
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = [{"message_id": 1, "status": "Pending"}]
    return resp


class SmsHelperTests(TestCase):
    def test_numbers(self):
        for raw in ("0917 123 4567", "+63 917 123 4567", "639171234567", "9171234567"):
            self.assertEqual(normalize_ph_mobile(raw), "09171234567", raw)
        for raw in ("", None, "12345", "02 8123 4567", "+1 415 555 0100"):  # landline, foreign
            self.assertIsNone(normalize_ph_mobile(raw), raw)
        self.assertEqual(mask_mobile("09171234567"), "0917 *** 4567")

    def test_one_segment_and_prefix(self):
        msg = fit_message("TEST " + "x" * 400)
        self.assertTrue(msg.startswith("NutriMatch: "))  # Semaphore drops texts starting with "TEST"
        self.assertLessEqual(len(msg), 160)
        self.assertEqual(fit_message("Pay ₱800.00 — today"), "NutriMatch: Pay P800.00 - today")

    @override_settings(SEMAPHORE_API_KEY="")
    def test_no_key_sends_nothing(self):
        with mock.patch("communication.sms.httpx.post") as post:
            self.assertFalse(send_sms("09171234567", "hello"))
        post.assert_not_called()

    @override_settings(SEMAPHORE_API_KEY="k", SEMAPHORE_SENDER_NAME="NUTRIMATCH")
    def test_send_and_failures(self):
        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post:
            self.assertTrue(send_sms("+63 917 123 4567", "hello"))
        data = post.call_args.kwargs["data"]
        self.assertEqual((data["number"], data["sendername"], data["message"]), ("09171234567", "NUTRIMATCH", "NutriMatch: hello"))
        # An invalid number never calls Semaphore; a network error is swallowed.
        with mock.patch("communication.sms.httpx.post") as post:
            self.assertFalse(send_sms("12345", "hello"))
            post.assert_not_called()
        with mock.patch("communication.sms.httpx.post", side_effect=RuntimeError("down")):
            self.assertFalse(send_sms("09171234567", "hello"))


@override_settings(SEMAPHORE_API_KEY="k")
class SmsReminderTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@sms.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.c = onboard_client(User.objects.create_user(email="c@sms.ph", password="x", role="client", first_name="Ana", last_name="Cruz",
                                                         phone="0917 123 4567"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")

    def _sent(self, post):
        return [c.kwargs["data"]["message"] for c in post.call_args_list]

    def test_settings_need_a_mobile_number(self):
        api = APIClient()
        api.force_authenticate(self.c)
        data = api.get("/api/client/reminder-settings/").data
        self.assertEqual((data["sms"], data["sms_number"]), (False, "0917 *** 4567"))
        self.assertTrue(api.put("/api/client/reminder-settings/", {"sms": True}, format="json").data["sms"])
        User.objects.filter(pk=self.c.pk).update(phone="")
        self.assertEqual(api.put("/api/client/reminder-settings/", {"sms": True}, format="json").status_code, 400)

    def test_only_when_turned_on_and_never_health_details(self):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=NOW + timedelta(minutes=45), duration_minutes=60)
        Invoice.objects.create(relationship=self.rel, appointment=appt, amount=Decimal("800"), status="unpaid")
        plan = MealPlan.objects.create(relationship=self.rel, name="P", status="active")
        MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast", scheduled_time=time(7, 30), day_of_week=None)
        Reminder.objects.create(client=self.c, relationship=self.rel, created_by=self.rnd, title="Take metformin 500 mg",
                                message="After breakfast", send_at=NOW - timedelta(minutes=1), repeat="once")

        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post:
            run_due_reminders(now=NOW)
        post.assert_not_called()  # SMS is off by default

        Reminder.objects.filter(client=self.c, source_key__isnull=False).delete()  # let the automatic ones fire again
        Reminder.objects.filter(client=self.c, created_by=self.rnd).update(is_sent=False, send_at=NOW - timedelta(minutes=1))
        ReminderPreference.objects.filter(user=self.c).update(sms=True)
        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post:
            run_due_reminders(now=NOW)
        texts = self._sent(post)
        # Budget (user's call): 1-hour reminder + payment due only — no task
        # or meal-log texts (the task still reaches the app).
        self.assertEqual(len(texts), 2, texts)
        self.assertTrue(any("consultation with RND Maria Santos starts at" in t for t in texts))
        self.assertTrue(any("Please pay P800.00" in t for t in texts))
        self.assertFalse(any("metformin" in t.lower() or "task" in t.lower() for t in texts))
        self.assertTrue(all(len(t) <= 160 and t.startswith("NutriMatch: ") and not t.endswith("...") for t in texts))

    def test_24_hour_reminder_is_not_texted(self):
        Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=NOW + timedelta(hours=20), duration_minutes=60)
        ReminderPreference.objects.filter(user=self.c).update(sms=True)
        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post:
            self.assertEqual(run_due_reminders(now=NOW), 1)  # the in-app reminder still goes out
        post.assert_not_called()


@override_settings(SEMAPHORE_API_KEY="k")
class SmsBookingEventTests(TestCase):
    """Booking confirmed and RND / admin cancellations are texted (2026-10-19)."""

    def setUp(self):
        from decimal import Decimal as D

        from clinical.models import PreConsultationScreening
        from django.utils import timezone

        self.rnd = approve_rnd(User.objects.create_user(email="r2@sms.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.c = onboard_client(User.objects.create_user(email="c2@sms.ph", password="x", role="client", first_name="Ana", last_name="Cruz",
                                                         phone="+639171234567"))
        self.admin = User.objects.create_user(email="a2@sms.ph", password="x", role="admin")
        PreConsultationScreening.objects.create(client=self.c, height_cm=D("160"), weight_kg=D("60"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="pending")
        self.appt = Appointment.objects.create(relationship=self.rel, type="video", status="pending",
                                               scheduled_at=timezone.now() + timedelta(days=2), duration_minutes=60)
        ReminderPreference.for_user(self.c)
        ReminderPreference.objects.filter(user=self.c).update(sms=True)
        self.api = APIClient()

    def _texts(self, post):
        return [(c.kwargs["data"]["number"], c.kwargs["data"]["message"]) for c in post.call_args_list]

    def test_confirm_then_rnd_cancel(self):
        self.api.force_authenticate(self.rnd)
        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/").status_code, 200)
        [(number, msg)] = self._texts(post)
        self.assertEqual(number, "09171234567")
        self.assertIn("RND Maria Santos confirmed your consultation", msg)
        self.assertIn("Please pay P", msg)
        self.assertLessEqual(len(msg), 160)

        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            resp = self.api.patch(f"/api/rnd/appointments/{self.appt.id}/cancel/", {"reason": "I am sick with the flu today"}, format="json")
            self.assertEqual(resp.status_code, 200, resp.data)
        [(_, msg)] = self._texts(post)
        self.assertIn("RND Maria Santos cancelled your consultation", msg)
        self.assertNotIn("flu", msg)  # the reason stays in the app

    def test_admin_cancel_is_texted(self):
        Appointment.objects.filter(pk=self.appt.pk).update(status="confirmed")
        self.api.force_authenticate(self.admin)
        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            resp = self.api.post(f"/api/admin/appointments/{self.appt.id}/cancel/", {"reason": "Client asked through support"}, format="json")
            self.assertEqual(resp.status_code, 200, resp.data)
        [(_, msg)] = self._texts(post)
        self.assertIn("NutriMatch cancelled your consultation with RND Maria Santos", msg)

    def test_nothing_when_sms_is_off_or_no_credit_key(self):
        ReminderPreference.objects.filter(user=self.c).update(sms=False)
        self.api.force_authenticate(self.rnd)
        with mock.patch("communication.sms.httpx.post", return_value=_ok_response()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            self.api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")
        post.assert_not_called()
