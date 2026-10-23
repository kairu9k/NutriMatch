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


class CancelledFirstBookingTests(TestCase):
    """A client whose first booking is cancelled before any consultation isn't
    the RND's patient: off My Patients, no NCP, free to book another RND
    (2026-10-23)."""

    def setUp(self):
        from decimal import Decimal

        from clinical.models import PreConsultationScreening

        self.rnd = approve_rnd(User.objects.create_user(email="r@x.ph", password="x", role="rnd", first_name="Rosa", last_name="V"))
        self.other = approve_rnd(User.objects.create_user(email="o@x.ph", password="x", role="rnd", first_name="Jose", last_name="R"))
        self.client_user = onboard_client(User.objects.create_user(email="c@x.ph", password="x", role="client", first_name="Lea", last_name="D"))
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=Decimal("158"), weight_kg=Decimal("74"))
        self.c, self.r = APIClient(), APIClient()
        self.c.force_authenticate(self.client_user)
        self.r.force_authenticate(self.rnd)

    def book(self):
        resp = self.c.post("/api/client/appointments/", {"rnd_id": self.rnd.id, "type": "video", "duration_minutes": 60,
                                                         "scheduled_at": booking_slot(2).isoformat()}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        return resp.data["id"], RndClientRelationship.objects.get(rnd=self.rnd, client=self.client_user)

    def patients(self):
        return [p["id"] for p in self.r.get("/api/rnd/patients/").data]

    def assert_not_a_patient(self, rel):
        rel.refresh_from_db()
        self.assertEqual(rel.status, "pending")
        self.assertNotIn(rel.id, self.patients())
        self.assertEqual(self.r.get(f"/api/rnd/relationships/{rel.id}/summary/").status_code, 404)
        resp = self.r.post(f"/api/rnd/relationships/{rel.id}/ncp/", {"relationship": rel.id, "encounter_date": "2026-10-23"}, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertIsNone(current_rnd_relationship(self.client_user, exclude_rnd_id=self.other.id))

    def test_client_cancels_waiting_first_booking(self):
        appt, rel = self.book()
        self.assertIn(rel.id, self.patients())  # a booking is waiting: shown as a new booking
        self.assertEqual(self.r.post(f"/api/rnd/relationships/{rel.id}/ncp/", {"relationship": rel.id, "encounter_date": "2026-10-23"},
                                     format="json").status_code, 403)  # not confirmed yet
        self.assertEqual(self.c.patch(f"/api/client/appointments/{appt}/cancel/", {}, format="json").status_code, 200)
        self.assert_not_a_patient(rel)

    def test_client_cancels_confirmed_first_booking(self):
        appt, rel = self.book()
        self.assertEqual(self.r.patch(f"/api/rnd/appointments/{appt}/confirm/", format="json").status_code, 200)
        rel.refresh_from_db()
        self.assertEqual(rel.status, "active")
        self.assertEqual(self.c.patch(f"/api/client/appointments/{appt}/cancel/", {}, format="json").status_code, 200)
        self.assert_not_a_patient(rel)

    def test_cancel_after_a_completed_consultation_keeps_the_patient(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        Appointment.objects.create(relationship=rel, type="video", status="completed", scheduled_at=timezone.now() - timedelta(days=7))
        appt = Appointment.objects.create(relationship=rel, type="video", status="pending", scheduled_at=booking_slot(2))
        self.assertEqual(self.c.patch(f"/api/client/appointments/{appt.id}/cancel/", {}, format="json").status_code, 200)
        rel.refresh_from_db()
        self.assertEqual(rel.status, "active")
        self.assertIn(rel.id, self.patients())

    def test_unconfirmed_request_whose_time_passed(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        appt = Appointment.objects.create(relationship=rel, type="video", status="pending", scheduled_at=booking_slot(2))
        self.assertIn(rel.id, self.patients())
        Appointment.objects.filter(pk=appt.pk).update(scheduled_at=timezone.now() - timedelta(hours=2))
        self.assert_not_a_patient(rel)
        # Still on the RND's Requests tab so they can decline it.
        board = self.r.get("/api/rnd/appointments/board/").data
        self.assertTrue(any(a["id"] == appt.id and a["time_passed"] for a in board["requests"]))


class ClientCancelCutoffTests(TestCase):
    """A client can't cancel a confirmed consultation once it has started
    (2026-10-23); a past unconfirmed request can still be withdrawn."""

    def test_cutoff(self):
        rnd = approve_rnd(User.objects.create_user(email="r@k.ph", password="x", role="rnd", first_name="R", last_name="K"))
        client = onboard_client(User.objects.create_user(email="c@k.ph", password="x", role="client", first_name="C", last_name="K"))
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")
        api = APIClient()
        api.force_authenticate(client)
        started = Appointment.objects.create(relationship=rel, type="video", status="confirmed",
                                             scheduled_at=timezone.now() - timedelta(minutes=5))
        resp = api.patch(f"/api/client/appointments/{started.id}/cancel/", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already started", resp.data["detail"])
        ahead = Appointment.objects.create(relationship=rel, type="video", status="confirmed", scheduled_at=booking_slot(2))
        self.assertEqual(api.patch(f"/api/client/appointments/{ahead.id}/cancel/", {}, format="json").status_code, 200)
        lapsed = Appointment.objects.create(relationship=rel, type="video", status="pending",
                                            scheduled_at=timezone.now() - timedelta(minutes=5))
        self.assertEqual(api.patch(f"/api/client/appointments/{lapsed.id}/cancel/", {}, format="json").status_code, 200)
