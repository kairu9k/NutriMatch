"""Rescheduling a paid consultation the RND can't make (2026-11-16)."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from billing.models import Invoice
from billing.services import expire_unpaid_appointments
from communication.models import Reminder

from profiles.models import RndAvailabilitySchedule

from .models import Appointment, RescheduleProposal
from .test_no_shows import _ConsultationSetup


def _hour(hours_from_now):
    return (timezone.now() + timedelta(hours=hours_from_now)).replace(minute=0, second=0, microsecond=0)


class RescheduleTests(_ConsultationSetup, TestCase):
    def setUp(self):
        super().setUp()
        # no weekly hours = any time fits, so the tests don't depend on the clock
        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()

    def offer(self, appt, at, **extra):
        return self.rnd_api.post(f"/api/rnd/appointments/{appt.id}/reschedule/",
                                 {"action": "offer", "scheduled_at": at.isoformat(), "reason": "I have a clinic emergency.", **extra},
                                 format="json")

    def client_answer(self, appt, action, at=None):
        data = {"action": action}
        if at:
            data["scheduled_at"] = at.isoformat()
        return self.client_api.post(f"/api/client/appointments/{appt.id}/reschedule/", data, format="json")

    def rnd_answer(self, appt, action, at=None):
        data = {"action": action}
        if at:
            data["scheduled_at"] = at.isoformat()
        return self.rnd_api.post(f"/api/rnd/appointments/{appt.id}/reschedule/", data, format="json")

    def invoice(self, appt):
        return Invoice.objects.get(appointment=appt)

    def test_offer_then_accept_moves_the_same_paid_consultation(self):
        a = self.appt(24 * 60)
        Reminder.objects.create(client=self.client_user, source_key=f"appt:{a.id}:24h", title="t", message="m",
                                type=Reminder.Type.APPOINTMENT, send_at=timezone.now(), is_sent=True)
        new = _hour(72)
        resp = self.offer(a, new)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "rescheduling")
        self.assertEqual(resp.data["reschedule"]["turn"], "client")
        self.assertEqual(resp.data["reschedule"]["proposals_left"], 2)
        self.assertEqual(self.invoice(a).status, "paid")

        resp = self.client_answer(a, "accept")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", new))
        self.assertEqual(self.invoice(a).status, "paid")  # same invoice, no new payment
        self.assertEqual(Invoice.objects.filter(appointment=a).count(), 1)
        self.assertFalse(Reminder.objects.filter(source_key__startswith=f"appt:{a.id}:").exists())

    def test_only_paid_confirmed_can_be_offered(self):
        unpaid = self.appt(24 * 60, paid=False)
        self.assertEqual(self.offer(unpaid, _hour(72)).status_code, 400)
        pending = self.appt(26 * 60, status="pending")
        self.assertEqual(self.offer(pending, _hour(73)).status_code, 400)

    def test_new_time_rules(self):
        a = self.appt(24 * 60)
        self.assertEqual(self.offer(a, timezone.now() + timedelta(minutes=60)).status_code, 400)  # too soon
        self.assertEqual(self.offer(a, _hour(24 * 15)).status_code, 400)  # beyond 14 days
        earlier = self.offer(a, _hour(5))
        self.assertEqual(earlier.status_code, 400)  # before the current time
        self.assertIn("after the consultation's current time", str(earlier.data))
        other = self.appt(4 * 24 * 60)
        self.assertEqual(self.offer(a, other.scheduled_at).status_code, 400)  # clashes with a booking
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/reschedule/",
                                 {"action": "offer", "scheduled_at": _hour(72).isoformat(), "reason": "short"}, format="json")
        self.assertEqual(resp.status_code, 400)  # reason under 10 characters

    def test_waiting_proposal_holds_its_slot(self):
        a = self.appt(24 * 60)
        held = _hour(72)
        self.offer(a, held)
        b = self.appt(2 * 24 * 60)
        self.assertEqual(self.offer(b, held).status_code, 400)
        slots = self.client_api.get(f"/api/client/rnds/{self.rnd.id}/booked-slots/").data
        self.assertTrue(any(s["start"] == held for s in slots))

    def test_counter_proposals_limited_to_three(self):
        a = self.appt(24 * 60)
        self.offer(a, _hour(50))
        self.assertEqual(self.client_answer(a, "propose", _hour(60)).status_code, 200)
        self.assertEqual(self.client_answer(a, "accept").status_code, 400)  # not their turn
        self.assertEqual(self.rnd_answer(a, "propose", _hour(70)).status_code, 200)
        resp = self.client_answer(a, "propose", _hour(80))
        self.assertEqual(resp.status_code, 400)  # third proposal was the last
        self.assertEqual(self.client_answer(a, "accept").status_code, 200)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", _hour(70)))
        self.assertEqual(list(a.reschedule_proposals.values_list("status", flat=True)), ["countered", "countered", "accepted"])

    def test_client_refund_any_time(self):
        a = self.appt(24 * 60)
        self.offer(a, _hour(72))
        resp = self.client_answer(a, "refund")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.cancelled_by), ("cancelled", "rnd"))
        self.assertEqual(self.invoice(a).status, "refund_pending")

    def test_rnd_cancel_while_rescheduling_refunds(self):
        a = self.appt(24 * 60)
        self.offer(a, _hour(72))
        self.client_answer(a, "propose", _hour(80))
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/cancel/", {"reason": "I can't do any time this week."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(self.invoice(a).status, "refund_pending")
        self.assertFalse(RescheduleProposal.objects.filter(appointment=a, status="waiting").exists())

    def test_unanswered_proposal_expires_with_refund(self):
        a = self.appt(24 * 60)
        self.offer(a, _hour(72))
        RescheduleProposal.objects.filter(appointment=a).update(expires_at=timezone.now() - timedelta(minutes=1))
        expire_unpaid_appointments(relationship=self.rel)
        a.refresh_from_db()
        self.assertEqual(a.status, "cancelled")
        self.assertEqual(self.invoice(a).status, "refund_pending")
        self.assertEqual(a.reschedule_proposals.get().status, "expired")

    def test_answer_waits_48_hours_or_until_an_hour_before(self):
        a = self.appt(3 * 60)
        near = _hour(5)
        self.offer(a, near)
        p = a.reschedule_proposals.get()
        self.assertEqual(p.expires_at, near - timedelta(minutes=60))
        b = self.appt(2 * 24 * 60)
        self.offer(b, _hour(24 * 10))
        q = b.reschedule_proposals.get()
        self.assertAlmostEqual((q.expires_at - q.created_at).total_seconds(), 48 * 3600, delta=5)

    def test_late_move_still_counts_as_late_cancel(self):
        a = self.appt(20)
        self.assertEqual(self.offer(a, _hour(48)).status_code, 400)  # needs a category
        resp = self.offer(a, _hour(48), category="emergency")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertTrue(a.cancelled_late)

    def test_rescheduling_pauses_the_room_and_blocks_discharge(self):
        from .discharge import discharge_blockers

        a = self.appt(10)
        self.offer(a, _hour(48), category="technical")
        a.refresh_from_db()
        self.assertEqual(self.client_api.get(f"/api/appointments/{a.id}/call-config/").status_code, 403)
        self.assertTrue(discharge_blockers(self.rel))
        expire_unpaid_appointments(relationship=self.rel)  # paid: the pay deadline doesn't touch it
        a.refresh_from_db()
        self.assertEqual(a.status, "rescheduling")

    def test_slots_endpoint(self):
        from datetime import time

        for day in range(7):
            RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=day, start_time=time(8), end_time=time(17),
                                                   effective_from=timezone.now().date() - timedelta(days=1))
        a = self.appt(24 * 60)
        resp = self.client_api.get(f"/api/appointments/{a.id}/reschedule/slots/")
        self.assertEqual(resp.status_code, 200)
        from datetime import datetime

        starts = [datetime.fromisoformat(x) for x in resp.data["slots"]]
        self.assertTrue(starts)
        now = timezone.now()
        self.assertTrue(all(now + timedelta(hours=2) <= x <= now + timedelta(days=14) for x in starts))
        self.assertTrue(all(x > a.scheduled_at for x in starts))  # later times only
        self.assertEqual(self.admin_api.get(f"/api/appointments/{a.id}/reschedule/slots/").status_code, 403)
