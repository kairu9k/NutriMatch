"""One RND at a time: a client can book a different RND only after their
current RND discharges them."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, booking_slot, onboard_client

from .models import Appointment, RndClientRelationship
from .services import current_rnd_relationship


class OneRndAtATimeTests(TestCase):
    def setUp(self):
        self.a = approve_rnd(User.objects.create_user(email="a@o.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.b = approve_rnd(User.objects.create_user(email="b@o.ph", password="x", role="rnd", first_name="Jose", last_name="Reyes"))
        self.c = onboard_client(User.objects.create_user(email="c@o.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.api = APIClient()
        self.api.force_authenticate(self.c)

    def test_active_rnd_blocks_another_until_discharged(self):
        rel = RndClientRelationship.objects.create(rnd=self.a, client=self.c, status="active")
        self.assertEqual(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id), rel)
        detail = self.api.get(f"/api/client/rnds/{self.b.id}/").data
        self.assertEqual(detail["booking_blocked_by"]["name"], "Maria Santos")
        self.assertIsNone(self.api.get(f"/api/client/rnds/{self.a.id}/").data["booking_blocked_by"])  # own RND is fine
        rel.status = "discharged"
        rel.save()
        self.assertIsNone(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id))
        self.assertIsNone(self.api.get(f"/api/client/rnds/{self.b.id}/").data["booking_blocked_by"])

    def test_waiting_first_booking_blocks_but_a_declined_one_does_not(self):
        rel = RndClientRelationship.objects.create(rnd=self.a, client=self.c, status="pending")
        appt = Appointment.objects.create(relationship=rel, type="video", status="pending", scheduled_at=timezone.now() + timedelta(days=1))
        self.assertEqual(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id), rel)
        appt.status = "cancelled"
        appt.save()
        self.assertIsNone(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id))

    def test_booking_api_refuses_a_second_rnd(self):
        RndClientRelationship.objects.create(rnd=self.a, client=self.c, status="active")
        resp = self.api.post("/api/client/appointments/", {
            "rnd_id": self.b.id, "type": "video", "duration_minutes": 60,
            "scheduled_at": booking_slot(2).isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("discharges you", str(resp.data))


class EndedConversationListTests(TestCase):
    """Messages lists discharged care too (?include=ended), read-only."""

    def test_include_ended(self):
        rnd = approve_rnd(User.objects.create_user(email="r@e.ph", password="x", role="rnd", first_name="R", last_name="E"))
        client = onboard_client(User.objects.create_user(email="c@e.ph", password="x", role="client", first_name="C", last_name="E"))
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="discharged")
        for user, url in ((client, "/api/client/relationships/"), (rnd, "/api/rnd/relationships/active/")):
            api = APIClient()
            api.force_authenticate(user)
            self.assertEqual(api.get(url).data, [])  # pickers: active only
            self.assertEqual([r["id"] for r in api.get(url, {"include": "ended"}).data], [rel.id])
            # History is readable; sending stays closed.
            self.assertEqual(api.get(f"/api/relationships/{rel.id}/messages/").status_code, 200)
            self.assertEqual(api.post(f"/api/relationships/{rel.id}/messages/", {"message": "hi"}, format="json").status_code, 403)


class ChatOnlyAfterConfirmTests(TestCase):
    """Chat is open only while care is active: closed after a discharge, still
    closed while a new booking waits, open once the RND confirms; a declined
    re-booking puts the care back to discharged (2026-10-15)."""

    def test_rebook_flow(self):
        from decimal import Decimal

        from clinical.models import PreConsultationScreening

        rnd = approve_rnd(User.objects.create_user(email="r@q.ph", password="x", role="rnd", first_name="Rosa", last_name="V"))
        client = onboard_client(User.objects.create_user(email="c@q.ph", password="x", role="client", first_name="Lea", last_name="D"))
        PreConsultationScreening.objects.create(client=client, height_cm=Decimal("158"), weight_kg=Decimal("74"))
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="discharged", discharge_reason="Goal reached, all done.")
        c, r = APIClient(), APIClient()
        c.force_authenticate(client)
        r.force_authenticate(rnd)
        msgs = f"/api/relationships/{rel.id}/messages/"

        def can_send(api):
            return api.post(msgs, {"message": "hi"}, format="json").status_code == 201

        def listed(api, url):
            return rel.id in [x["id"] for x in api.get(url, {"include": "ended"}).data]

        def book(hour):
            resp = c.post("/api/client/appointments/", {"rnd_id": rnd.id, "type": "video", "duration_minutes": 60,
                                                        "scheduled_at": booking_slot(2, hour).isoformat()}, format="json")
            self.assertEqual(resp.status_code, 201, resp.data)
            return resp.data["id"]

        self.assertFalse(can_send(c) or can_send(r))  # discharged

        first = book(10)  # waiting for the RND: still closed, but the history stays listed
        rel.refresh_from_db()
        self.assertEqual(rel.status, "pending")
        self.assertFalse(can_send(c) or can_send(r))
        self.assertTrue(listed(c, "/api/client/relationships/") and listed(r, "/api/rnd/relationships/active/"))

        self.assertEqual(r.patch(f"/api/rnd/appointments/{first}/cancel/", {"reason": "Fully booked that day."}, format="json").status_code, 200)
        rel.refresh_from_db()
        self.assertEqual(rel.status, "discharged")  # declined: back to discharged
        self.assertFalse(can_send(c))

        second = book(11)
        self.assertEqual(r.patch(f"/api/rnd/appointments/{second}/confirm/", format="json").status_code, 200)
        rel.refresh_from_db()
        self.assertEqual(rel.status, "active")
        self.assertTrue(can_send(c) and can_send(r))  # confirmed: chat open both ways
