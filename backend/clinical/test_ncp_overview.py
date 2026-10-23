"""NCP Records page overview: worklist rules and record list."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship
from scheduling.patient_insights import ph_tz

from .models import NcpRecord, PreConsultationScreening
from .ncp_overview import build_ncp_overview


class NcpOverviewTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@o.ph", password="x", role="rnd", first_name="M", last_name="S"))
        self.today = timezone.now().astimezone(ph_tz()).date()  # the app counts days in PH time

    def _patient(self, email, nrs=1):
        c = onboard_client(User.objects.create_user(email=email, password="x", role="client", first_name=email[:3], last_name="C"))
        PreConsultationScreening.objects.create(client=c, height_cm=Decimal("160"), weight_kg=Decimal("60"), nrs_score=nrs)
        return RndClientRelationship.objects.create(rnd=self.rnd, client=c, status="active")

    def _final(self, rel, days_ago, **kw):
        return NcpRecord.objects.create(relationship=rel, status="completed", encounter_date=self.today - timedelta(days=days_ago), **kw)

    def _visit(self, rel, days_ago=1):
        return Appointment.objects.create(relationship=rel, type="video", status="completed", scheduled_at=timezone.now() - timedelta(days=days_ago))

    def test_worklist_rules(self):
        new = self._patient("new@o.ph")
        self._visit(new)
        risky = self._patient("risk@o.ph", nrs=4)
        self._visit(risky)
        booked = self._patient("bkd@o.ph")  # confirmed, consultation not held yet: no record expected
        Appointment.objects.create(relationship=booked, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(days=1))
        old = self._patient("old@o.ph")
        self._final(old, 30)
        recent = self._patient("rec@o.ph")
        self._final(recent, 5)
        unrec = self._patient("unr@o.ph")
        self._final(unrec, 10)
        Appointment.objects.create(relationship=unrec, type="video", status="completed", scheduled_at=timezone.now() - timedelta(days=2))
        drafting = self._patient("dra@o.ph")
        NcpRecord.objects.create(relationship=drafting, encounter_date=self.today, weight_kg=Decimal("60"), height_cm=Decimal("160"))

        d = build_ncp_overview(self.rnd)
        w = d["worklist"]
        self.assertEqual([x["relationship_id"] for x in w["no_record"]], [risky.id, new.id])  # at-risk first, not the booked one
        self.assertIsNotNone(w["no_record"][0]["visit_date"])
        due = {x["relationship_id"]: x["reason"] for x in w["follow_up_due"]}
        self.assertEqual(set(due), {old.id, unrec.id})
        self.assertIn("30 days", due[old.id])
        self.assertIn("has no NCP record", due[unrec.id])
        self.assertEqual(w["drafts"][0]["relationship_id"], drafting.id)
        self.assertIn("PES problem", w["drafts"][0]["missing"])
        self.assertEqual(d["summary"]["follow_up_due"], 2)

    def test_follow_up_numbering(self):
        rel = self._patient("num@o.ph")
        self._final(rel, 60)
        self._final(rel, 30)
        NcpRecord.objects.create(relationship=rel, encounter_date=self.today)
        rows = build_ncp_overview(self.rnd)["records"]
        self.assertEqual([(r["is_follow_up"], r["follow_up_no"]) for r in rows], [(True, 2), (True, 1), (False, None)])

    def test_own_records_only(self):
        rel = self._patient("own@o.ph")
        self._final(rel, 1)
        other = approve_rnd(User.objects.create_user(email="x@o.ph", password="x", role="rnd", first_name="X", last_name="R"))
        api = APIClient()
        api.force_authenticate(other)
        resp = api.get("/api/rnd/ncp/overview/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["records"], [])
