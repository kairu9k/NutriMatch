"""How a consultation closes (2026-11-16): the call's attendance record decides
(scheduling/closing.py), the room keeps to the schedule (no overtime), and
nothing stays open for ever."""

import json
from datetime import timedelta
from unittest import mock

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from billing.models import Invoice
from billing.services import expire_unpaid_appointments
from communication.models import NotificationLog
from communication.reminders import run_rnd_reminders

from .attendance import record_presence
from .closing import auto_close_due, close_options, open_too_long
from .consumers import CallConsumer
from .models import Appointment
from .test_no_shows import _ConsultationSetup
from .test_video_call import _setup as _call_setup
from .video_call import CallDenied, call_access


class ClosingTests(_ConsultationSetup, TestCase):
    def meet(self, a, minutes):
        """Both in the call together for `minutes`, from the start."""
        t0 = a.scheduled_at
        record_presence(a.id, "rnd", True, ["rnd"], now=t0)
        record_presence(a.id, "client", True, ["rnd", "client"], now=t0)
        record_presence(a.id, "client", False, ["rnd"], now=t0 + timedelta(minutes=minutes))
        record_presence(a.id, "rnd", False, [], now=t0 + timedelta(minutes=minutes))

    def waited(self, a, minutes=6):
        """Only the RND, in the call for a while."""
        t0 = a.scheduled_at
        record_presence(a.id, "rnd", True, ["rnd"], now=t0)
        record_presence(a.id, "rnd", False, [], now=t0 + timedelta(minutes=minutes))

    def only_client(self, a, minutes=10):
        t0 = a.scheduled_at
        record_presence(a.id, "client", True, ["client"], now=t0)
        record_presence(a.id, "client", False, [], now=t0 + timedelta(minutes=minutes))

    def reload(self, a):
        a.refresh_from_db()
        return a

    # ---- what the call record allows
    def test_options_follow_the_call_record(self):
        a = self.appt(-70)
        self.assertEqual(close_options(a), {"complete": False, "no_show": False, "refund": True})  # nobody came
        self.waited(a)
        self.assertEqual(close_options(self.reload(a)), {"complete": False, "no_show": True, "refund": True})
        b = self.appt(-75)
        self.meet(b, 4)
        self.assertFalse(close_options(self.reload(b))["complete"])  # together too briefly
        c = self.appt(-80)
        self.meet(c, 5)
        self.assertEqual(close_options(self.reload(c)), {"complete": True, "no_show": False, "refund": True})
        d = self.appt(-90, type_="in_person")
        self.assertEqual(close_options(d), {"complete": True, "no_show": True, "refund": True})  # the RND's word

    def test_mark_complete_needs_five_minutes_together(self):
        a = self.appt(-30)
        self.meet(a, 3)
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/complete/")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("5 minutes", str(resp.data))
        self.assertEqual(self.reload(a).status, "confirmed")
        b = self.appt(-31)
        self.meet(b, 6)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{b.id}/complete/").status_code, 200)
        c = self.appt(-90, type_="in_person")  # no record: the RND's word
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{c.id}/complete/").status_code, 200)

    def test_no_show_needs_the_rnd_to_have_waited(self):
        a = self.appt(-20)
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("waited in the video call", str(resp.data))
        self.waited(a)
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json").status_code, 200)

    def test_no_show_waits_fifteen_minutes_after_the_start(self):
        """Joining the room early isn't waiting: the client has until start + 15 minutes."""
        a = self.appt(-10)  # started 10 minutes ago
        record_presence(a.id, "rnd", True, ["rnd"], now=a.scheduled_at - timedelta(minutes=15))  # the RND has been in since the room opened
        self.assertFalse(close_options(self.reload(a))["no_show"])
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("15 minutes after the start", str(resp.data))
        Appointment.objects.filter(pk=a.pk).update(scheduled_at=timezone.now() - timedelta(minutes=16))
        self.assertTrue(close_options(self.reload(a))["no_show"])
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json").status_code, 200)
        # the payload tells the room when it opens
        b = self.appt(-5)
        data = self.rnd_api.get(f"/api/rnd/appointments/{b.id}/").data
        self.assertEqual(data["no_show_opens_at"][:16], (b.scheduled_at + timedelta(minutes=15)).isoformat()[:16])

    def test_in_person_no_show_waits_too(self):
        early = self.appt(-10, type_="in_person")
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{early.id}/no-show/", {}, format="json").status_code, 400)
        later = self.appt(-20, type_="in_person")
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{later.id}/no-show/", {}, format="json").status_code, 200)

    def test_call_failed_counts_as_a_late_cancel_when_only_the_client_was_there(self):
        a = self.appt(-20)
        self.only_client(a)
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{a.id}/call-failed/", {}, format="json").status_code, 200)
        a = self.reload(a)
        self.assertEqual((a.status, a.cancelled_late), ("cancelled", True))
        self.assertEqual(Invoice.objects.get(appointment=a).status, "refund_pending")
        b = self.appt(-21)  # a real call that broke: both were there for a while
        self.meet(b, 8)
        self.rnd_api.post(f"/api/rnd/appointments/{b.id}/call-failed/", {}, format="json")
        self.assertFalse(self.reload(b).cancelled_late)

    # ---- closing by itself
    def test_a_real_consultation_completes_by_itself_when_the_room_closes(self):
        a = self.appt(-70)  # ended 10 minutes ago
        self.meet(a, 25)
        self.assertEqual(auto_close_due(), 1)
        a = self.reload(a)
        self.assertEqual(a.status, "completed")
        self.assertIsNotNone(a.completed_at)  # the payout hold starts
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, subject="Your consultation summary is ready").exists())
        self.assertEqual(auto_close_due(), 0)  # once

    def test_nothing_closes_before_the_end(self):
        running = self.appt(-30)
        self.meet(running, 12)
        self.assertEqual(auto_close_due(), 0)  # still running
        self.assertEqual(self.reload(running).status, "confirmed")

    def test_when_the_room_closes_a_no_show_or_a_refund_closes_by_itself(self):
        """The record answers every case, so nothing waits for a button (user's call, 2026-11-16)."""
        waited = self.appt(-70)
        self.waited(waited)
        nobody = self.appt(-75)
        absent = self.appt(-80)
        self.only_client(absent)
        self.assertEqual(auto_close_due(), 3)
        self.assertEqual(self.reload(waited).status, "no_show")  # the RND waited: the client can still dispute it
        nobody, absent = self.reload(nobody), self.reload(absent)
        self.assertEqual((nobody.status, nobody.cancelled_by, nobody.cancelled_late), ("cancelled", "system", False))
        self.assertEqual((absent.status, absent.cancelled_by, absent.cancelled_late), ("cancelled", "rnd_absent", True))
        for a in (nobody, absent):
            self.assertEqual(Invoice.objects.get(appointment=a).status, "refund_pending")  # to the admin's refund list

    def test_it_runs_wherever_expired_appointments_are(self):
        a = self.appt(-70)
        self.meet(a, 25)
        expire_unpaid_appointments(relationship__rnd=self.rnd)
        self.assertEqual(self.reload(a).status, "completed")

    # ---- in-person: no record, so a person decides
    def test_in_person_never_closes_by_itself_and_reaches_the_admin(self):
        a = self.appt(-24 * 60 * 5, type_="in_person")
        self.assertEqual(auto_close_due(), 0)
        self.assertEqual(self.reload(a).status, "confirmed")
        self.assertEqual([x.id for x in open_too_long()], [a.id])
        recent = self.appt(-24 * 60 * 2, type_="in_person")
        self.assertNotIn(recent.id, [x.id for x in open_too_long()])

    def test_client_can_dispute_a_completed_in_person_visit_but_not_a_video_call(self):
        a = self.appt(-90, type_="in_person")
        self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/complete/")
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/dispute/", {"reason": "Nobody was at the clinic for me."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        v = self.appt(-80)
        self.meet(v, 20)
        self.rnd_api.patch(f"/api/rnd/appointments/{v.id}/complete/")
        resp = self.client_api.post(f"/api/client/appointments/{v.id}/dispute/", {"reason": "Nobody was at the clinic for me."}, format="json")
        self.assertEqual(resp.status_code, 400)  # the call record proves it

    # ---- reminders
    def test_the_rnd_is_reminded_the_day_after_for_in_person_visits(self):
        a = self.appt(-24 * 60 - 90, type_="in_person")  # ended more than a day ago
        fresh = self.appt(-90, type_="in_person")
        self.assertEqual(run_rnd_reminders(rnd=self.rnd), 1)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, notifiable_id=a.id, subject="Close your consultation").exists())
        self.assertFalse(NotificationLog.objects.filter(notifiable_id=fresh.id, subject="Close your consultation").exists())
        self.assertEqual(run_rnd_reminders(rnd=self.rnd), 0)  # once

    def test_admin_sees_old_open_in_person_visits(self):
        a = self.appt(-24 * 60 * 5, type_="in_person")
        resp = self.admin_api.get("/api/admin/dashboard/")
        self.assertEqual(resp.status_code, 200)
        items = {i["key"]: i for i in resp.data["attention"]}
        self.assertEqual(items["unclosed"]["count"], 1)
        self.assertEqual(items["unclosed"]["people"][0]["id"], a.relationship.rnd_id)


class NoOvertimeTests(TestCase):
    def setUp(self):
        _call_setup(self, minutes_from_now=-55)  # 60 minutes long: ends in 5 minutes

    def test_the_room_closes_at_the_scheduled_end(self):
        user, now = self.rnd, timezone.now()
        end = self.appt.scheduled_at + timedelta(minutes=60)
        self.assertEqual(call_access(user, self.appt.id, now=end - timedelta(seconds=1))[1], "rnd")
        with self.assertRaises(CallDenied) as ctx:
            call_access(user, self.appt.id, now=end + timedelta(seconds=1))
        self.assertEqual(ctx.exception.code, "closed")


class CallClockTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        _call_setup(self, minutes_from_now=-57)
        self.ends = timezone.now() + timedelta(seconds=3)
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=self.ends - timedelta(minutes=60))

    async def test_warnings_then_the_server_ends_the_call(self):
        comm = WebsocketCommunicator(CallConsumer.as_asgi(), f"/ws/appointments/{self.appt.id}/call/")
        comm.scope["user"] = self.rnd
        comm.scope["url_route"] = {"kwargs": {"appointment_id": str(self.appt.id)}}
        with mock.patch("scheduling.consumers.WRAP_UP_MINUTES", (0.03, 0.01)):  # 1.8 s and 0.6 s before the end
            connected, _ = await comm.connect()
            self.assertTrue(connected)
            self.assertEqual(json.loads(await comm.receive_from())["type"], "welcome")
            first = json.loads(await comm.receive_from(timeout=5))
            second = json.loads(await comm.receive_from(timeout=5))
            self.assertEqual((first["type"], first["minutes"]), ("time-left", 0.03))
            self.assertEqual((second["type"], second["minutes"]), ("time-left", 0.01))
            self.assertEqual(json.loads(await comm.receive_from(timeout=5))["type"], "ended")
            closed = await comm.receive_output(timeout=5)
        self.assertEqual((closed["type"], closed["code"]), ("websocket.close", 4011))
        # nobody can rejoin once it has ended
        again = WebsocketCommunicator(CallConsumer.as_asgi(), f"/ws/appointments/{self.appt.id}/call/")
        again.scope["user"] = self.rnd
        again.scope["url_route"] = {"kwargs": {"appointment_id": str(self.appt.id)}}
        await database_sync_to_async(lambda: None)()
        import asyncio

        await asyncio.sleep(0.5)
        connected, _ = await again.connect()
        # refused either way: the room closed, and the consultation itself closed from the call record
        self.assertIn(json.loads(await again.receive_from())["code"], ("closed", "not_confirmed"))
        closed = await database_sync_to_async(Appointment.objects.get)(pk=self.appt.pk)
        self.assertEqual(closed.status, "cancelled")  # nobody had been together for 5 minutes: refunded


class DisputeFromHelpFormTests(_ConsultationSetup, TestCase):
    """Help & Support is the one form for a dispute (2026-11-16): "Dispute a
    consultation" there does everything the old Dispute button did."""

    def no_show(self):
        a = self.appt(-30)
        record_presence(a.id, "rnd", True, ["rnd"], now=a.scheduled_at)
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json").status_code, 200)
        return a

    def send(self, appt_id, message="I was in the waiting room the whole time, my camera failed.", user_api=None):
        return (user_api or self.client_api).post("/api/support/tickets/", {
            "category": "dispute", "subject": "No-show dispute", "message": message, "appointment": appt_id,
        }, format="json")

    def test_the_form_opens_a_dispute_that_holds_the_payout(self):
        from billing.payouts import invoice_state
        from communication.models import SupportTicket

        a = self.no_show()
        links = self.client_api.get("/api/support/links/").data["appointments"]
        self.assertTrue(next(r for r in links if r["id"] == a.id)["can_dispute"])
        resp = self.send(a.id)
        self.assertEqual(resp.status_code, 201, resp.data)
        a = self.reload(a)
        self.assertIsNotNone(a.dispute_opened_at)
        self.assertEqual(SupportTicket.objects.get(pk=resp.data["id"]).category, "dispute")
        self.assertEqual(invoice_state(Invoice.objects.get(appointment=a), timezone.now() + timedelta(days=5)), "pending")  # held
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, subject="Consultation disputed").exists())
        links = self.client_api.get("/api/support/links/").data["appointments"]
        self.assertFalse(next(r for r in links if r["id"] == a.id)["can_dispute"])  # once
        self.assertEqual(self.send(a.id).status_code, 400)

    def test_the_form_checks_what_the_button_checked(self):
        a = self.no_show()
        self.assertEqual(self.send(None).status_code, 400)  # pick the consultation
        self.assertEqual(self.send(a.id, message="Too short.").status_code, 400)  # 20 characters
        self.assertEqual(self.send(a.id, user_api=self.rnd_api).status_code, 400)  # only the client
        completed = self.appt(-90)
        self.assertEqual(self.send(completed.id).status_code, 400)  # nothing to dispute
        Appointment.objects.filter(pk=a.pk).update(completed_at=timezone.now() - timedelta(days=3, minutes=1))
        resp = self.send(a.id)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("3 days", str(resp.data))

    def reload(self, a):
        a.refresh_from_db()
        return a
