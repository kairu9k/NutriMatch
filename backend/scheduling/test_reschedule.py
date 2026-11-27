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


class _Helpers(_ConsultationSetup):
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


class RescheduleTests(_Helpers, TestCase):
    def test_offer_then_accept_moves_the_same_paid_consultation(self):
        a = self.appt(24 * 60)
        Reminder.objects.create(client=self.client_user, source_key=f"appt:{a.id}:24h", title="t", message="m",
                                type=Reminder.Type.APPOINTMENT, send_at=timezone.now(), is_sent=True)
        new = _hour(72)
        resp = self.offer(a, new)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "rescheduling")
        self.assertEqual(resp.data["reschedule"]["turn"], "client")
        self.assertEqual(self.invoice(a).status, "paid")

        resp = self.client_answer(a, "accept")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", new))
        self.assertEqual(self.invoice(a).status, "paid")  # same invoice, no new payment
        self.assertEqual(Invoice.objects.filter(appointment=a).count(), 1)
        self.assertFalse(Reminder.objects.filter(source_key__startswith=f"appt:{a.id}:").exists())

    def test_a_pending_request_needs_a_screening_to_get_a_suggested_time(self):
        pending = self.appt(26 * 60, status="pending")
        self.assertEqual(self.offer(pending, _hour(73)).status_code, 400)

    def test_unpaid_confirmed_can_be_offered_too(self):
        # 2026-11-23 (adviser): paid or not, the RND can move a consultation as well
        a = self.appt(24 * 60, paid=False)
        new = _hour(72)
        resp = self.offer(a, new)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(self.client_answer(a, "accept").status_code, 200)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", new))
        self.assertEqual(self.invoice(a).status, "unpaid")  # still to pay, before the new time

    def test_unpaid_offer_unanswered_cancels_and_voids_the_invoice(self):
        a = self.appt(24 * 60, paid=False)
        self.offer(a, _hour(72))
        RescheduleProposal.objects.filter(appointment=a).update(expires_at=timezone.now() - timedelta(minutes=1))
        expire_unpaid_appointments(relationship=self.rel)
        a.refresh_from_db()
        self.assertEqual(a.status, "cancelled")
        self.assertEqual(self.invoice(a).status, "cancelled")  # nothing was paid, so nothing to refund

    def test_new_time_rules(self):
        a = self.appt(24 * 60)
        self.assertEqual(self.offer(a, timezone.now() + timedelta(minutes=60)).status_code, 400)  # too soon
        self.assertEqual(self.offer(a, _hour(24 * 16)).status_code, 400)  # beyond 14 days after the booked time
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

    def test_counter_proposals_are_not_limited(self):
        a = self.appt(24 * 60)
        self.offer(a, _hour(50))
        self.assertEqual(self.client_answer(a, "propose", _hour(60)).status_code, 200)
        self.assertEqual(self.client_answer(a, "accept").status_code, 400)  # not their turn
        self.assertEqual(self.rnd_answer(a, "propose", _hour(70)).status_code, 200)
        self.assertEqual(self.client_answer(a, "propose", _hour(80)).status_code, 200)  # a 4th is fine (2026-11-28)
        self.assertEqual(self.rnd_answer(a, "propose", _hour(90)).status_code, 200)
        self.assertEqual(self.client_answer(a, "accept").status_code, 200)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", _hour(90)))
        self.assertEqual(list(a.reschedule_proposals.values_list("status", flat=True)),
                         ["countered", "countered", "countered", "countered", "accepted"])

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
        self.assertTrue(all(now + timedelta(hours=2) <= x <= a.scheduled_at + timedelta(days=14) for x in starts))  # 14 days from the booked time
        self.assertTrue(all(x > a.scheduled_at for x in starts))  # later times only
        self.assertEqual(self.admin_api.get(f"/api/appointments/{a.id}/reschedule/slots/").status_code, 403)


class WindowTests(_Helpers, TestCase):
    """2026-11-23 (user's calls): the 14 days count from the booked time, and a
    consultation can't drift more than 14 days past the time first booked."""

    def test_booking_more_than_14_days_away_can_still_move(self):
        a = self.appt(20 * 24 * 60)
        self.assertEqual(self.offer(a, _hour(21 * 24)).status_code, 200)

    def test_new_time_at_most_14_days_after_the_booked_time(self):
        a = self.appt(20 * 24 * 60)
        self.assertEqual(self.offer(a, _hour(35 * 24)).status_code, 400)

    def test_drift_capped_14_days_past_the_first_booked_time(self):
        a = self.appt(24 * 60)
        self.offer(a, _hour(10 * 24))
        self.client_answer(a, "accept")
        a.refresh_from_db()
        self.assertEqual(self.offer(a, _hour(17 * 24)).status_code, 400)  # 16 days past the first booking
        self.assertEqual(self.offer(a, _hour(14 * 24)).status_code, 200)


class ClientRequestTests(_Helpers, TestCase):
    """2026-11-23 (adviser): the client can ask for a new time, paid or not;
    only the RND confirms it. Forward only, until 2 hours before; declined or
    unanswered keeps the original booking."""

    def ask(self, appt, at, note="Work came up that day."):
        return self.client_api.post(f"/api/client/appointments/{appt.id}/reschedule/",
                                    {"action": "request", "scheduled_at": at.isoformat(), "note": note}, format="json")

    def test_unpaid_request_accepted_by_the_rnd(self):
        a = self.appt(24 * 60, paid=False)
        new = _hour(72)
        resp = self.ask(a, new)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "rescheduling")
        self.assertEqual((resp.data["reschedule"]["turn"], resp.data["reschedule"]["started_by"]), ("rnd", "client"))
        self.assertEqual(self.rnd_answer(a, "accept").status_code, 200)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", new))
        self.assertEqual(self.invoice(a).status, "unpaid")  # still the same invoice to pay

    def test_paid_request_accepted_keeps_the_payment(self):
        a = self.appt(24 * 60)
        self.assertEqual(self.ask(a, _hour(72)).status_code, 200)
        self.assertEqual(self.rnd_answer(a, "accept").status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.scheduled_at, _hour(72))
        self.assertEqual(self.invoice(a).status, "paid")
        self.assertEqual(Invoice.objects.filter(appointment=a).count(), 1)

    def test_rnd_declines_and_the_original_stays(self):
        a = self.appt(24 * 60)
        original = a.scheduled_at
        self.ask(a, _hour(72))
        resp = self.rnd_answer(a, "decline")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", original))
        self.assertEqual(self.invoice(a).status, "paid")
        self.assertEqual(a.reschedule_proposals.get().status, "declined")

    def test_unanswered_request_keeps_the_original(self):
        a = self.appt(24 * 60)
        original = a.scheduled_at
        self.ask(a, _hour(72))
        RescheduleProposal.objects.filter(appointment=a).update(expires_at=timezone.now() - timedelta(minutes=1))
        expire_unpaid_appointments(relationship=self.rel)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", original))
        self.assertEqual(self.invoice(a).status, "paid")  # never a refund for the client's own request
        self.assertEqual(a.reschedule_proposals.get().status, "expired")

    def test_request_waits_until_an_hour_before_the_booked_time(self):
        a = self.appt(5 * 60)
        self.ask(a, _hour(72))
        self.assertEqual(a.reschedule_proposals.get().expires_at, a.scheduled_at - timedelta(minutes=60))

    def test_client_withdraws_and_the_original_stays(self):
        a = self.appt(24 * 60)
        self.ask(a, _hour(72))
        self.assertEqual(self.client_answer(a, "keep").status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.status, "confirmed")
        self.assertEqual(a.reschedule_proposals.get().status, "withdrawn")

    def test_rnd_counter_then_client_keeps_original(self):
        a = self.appt(24 * 60)
        original = a.scheduled_at
        self.ask(a, _hour(72))
        self.assertEqual(self.rnd_answer(a, "propose", _hour(80)).status_code, 200)
        self.assertEqual(self.client_answer(a, "refund").status_code, 400)  # their own request: no refund route
        self.assertEqual(self.client_answer(a, "keep").status_code, 200)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("confirmed", original))

    def test_request_rules(self):
        a = self.appt(24 * 60)
        self.assertEqual(self.ask(a, _hour(5)).status_code, 400)  # earlier than the booking
        soon = self.appt(90, paid=True)
        resp = self.ask(soon, _hour(72))
        self.assertEqual(resp.status_code, 400)  # less than 2 hours before
        self.assertIn("2 hours", str(resp.data))
        self.assertEqual(self.rnd_answer(a, "decline").status_code, 400)  # nothing to decline

    def test_rnd_cannot_decline_its_own_reschedule(self):
        a = self.appt(24 * 60)
        self.assertEqual(self.offer(a, _hour(72)).status_code, 200)
        self.assertEqual(self.rnd_answer(a, "decline").status_code, 400)
        self.assertEqual(self.client_answer(a, "keep").status_code, 400)  # the RND can't make the original

    def test_pending_request_changes_time_directly(self):
        a = self.appt(24 * 60, status="pending")
        new = _hour(72)
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/reschedule/",
                                    {"action": "change", "scheduled_at": new.isoformat()}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.scheduled_at), ("pending", new))
        earlier = self.client_api.post(f"/api/client/appointments/{a.id}/reschedule/",
                                       {"action": "change", "scheduled_at": _hour(30).isoformat()}, format="json")
        self.assertEqual(earlier.status_code, 400)


class RndSuggestsForRequestTests(_Helpers, TestCase):
    """2026-11-27 (adviser): the RND can move a request before confirming it too."""

    def setUp(self):
        from clinical.models import PreConsultationScreening

        super().setUp()
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=160, weight_kg=60, activity_level="sedentary")
        self.req = self.appt(26 * 60, status="pending")
        self.original = self.req.scheduled_at
        self.new = _hour(73)

    def test_suggest_keeps_it_pending_and_waits_for_the_client(self):
        resp = self.offer(self.req, self.new)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "pending")
        self.assertEqual(resp.data["reschedule"]["turn"], "client")
        self.assertFalse(Invoice.objects.filter(appointment=self.req).exists())
        self.assertEqual(self.rnd_answer(self.req, "accept").status_code, 400)  # it's the client's answer
        self.assertEqual(self.offer(self.req, _hour(74)).status_code, 400)  # one at a time

    def test_client_accepting_moves_and_confirms_it(self):
        self.offer(self.req, self.new)
        resp = self.client_answer(self.req, "accept")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.req.refresh_from_db()
        self.assertEqual((self.req.status, self.req.scheduled_at), ("confirmed", self.new))
        self.assertEqual(self.invoice(self.req).status, "unpaid")  # payment due now
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.status, "active")

    def test_client_keeping_their_time_leaves_the_request(self):
        self.offer(self.req, self.new)
        self.assertEqual(self.client_answer(self.req, "keep").status_code, 200)
        self.req.refresh_from_db()
        self.assertEqual((self.req.status, self.req.scheduled_at), ("pending", self.original))
        self.assertEqual(self.req.reschedule_proposals.get().status, RescheduleProposal.Status.DECLINED)
        # the RND can still confirm it as usual
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{self.req.id}/confirm/").status_code, 200)

    def test_rnd_confirming_the_original_closes_the_suggestion(self):
        self.offer(self.req, self.new)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{self.req.id}/confirm/").status_code, 200)
        self.assertEqual(self.req.reschedule_proposals.get().status, RescheduleProposal.Status.WITHDRAWN)
        self.assertEqual(self.client_answer(self.req, "accept").status_code, 400)

    def test_client_changing_time_replaces_the_suggestion(self):
        self.offer(self.req, self.new)
        mine = _hour(50)
        resp = self.client_api.post(f"/api/client/appointments/{self.req.id}/reschedule/",
                                    {"action": "change", "scheduled_at": mine.isoformat()}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.req.refresh_from_db()
        self.assertEqual((self.req.status, self.req.scheduled_at), ("pending", mine))
        self.assertEqual(self.req.reschedule_proposals.get().status, RescheduleProposal.Status.DECLINED)

    def test_unanswered_suggestion_expires_and_the_request_stays(self):
        self.offer(self.req, self.new)
        RescheduleProposal.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        expire_unpaid_appointments()
        self.req.refresh_from_db()
        self.assertEqual((self.req.status, self.req.scheduled_at), ("pending", self.original))
        self.assertEqual(self.req.reschedule_proposals.get().status, RescheduleProposal.Status.EXPIRED)

    def test_the_suggested_slot_is_held(self):
        from .reschedule import held_intervals

        self.offer(self.req, self.new)
        self.assertEqual([s for s, _ in held_intervals(rnd_id=self.rnd.id)], [self.new])
