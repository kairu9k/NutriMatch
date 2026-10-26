"""The WebRTC video call: who may join (call-config and the signaling socket),
the TURN credentials, and passing messages between the two people."""

import json
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from core.test_utils import approve_rnd, onboard_client

from .consumers import CallConsumer
from .models import Appointment, ConsultationSession, RndClientRelationship


def _setup(obj, *, minutes_from_now=5, paid=True, kind="video", status="confirmed"):
    obj.rnd = approve_rnd(User.objects.create_user(email="rnd@v.ph", password="x", role="rnd", first_name="Lena", last_name="T"))
    obj.client_user = onboard_client(User.objects.create_user(email="c@v.ph", password="x", role="client", first_name="Ana", last_name="C"))
    obj.outsider = onboard_client(User.objects.create_user(email="o@v.ph", password="x", role="client", first_name="Out", last_name="S"))
    rel = RndClientRelationship.objects.create(rnd=obj.rnd, client=obj.client_user, status="active")
    obj.appt = Appointment.objects.create(relationship=rel, type=kind, status=status, duration_minutes=60,
                                          scheduled_at=timezone.now() + timedelta(minutes=minutes_from_now))
    Invoice.objects.create(relationship=rel, appointment=obj.appt, amount=Decimal("800"),
                           status="paid" if paid else "unpaid", paid_at=timezone.now() if paid else None)


@override_settings(CLOUDFLARE_TURN_KEY_ID="", CLOUDFLARE_TURN_API_TOKEN="")
class CallConfigTests(TestCase):
    def setUp(self):
        _setup(self)

    def _get(self, user, appt=None):
        api = APIClient()
        api.force_authenticate(user)
        return api.get(f"/api/appointments/{(appt or self.appt).id}/call-config/")

    def test_both_people_get_the_config(self):
        rnd = self._get(self.rnd)
        self.assertEqual(rnd.status_code, 200, rnd.data)
        self.assertEqual((rnd.data["role"], rnd.data["other"]["name"]), ("rnd", "Ana C"))
        self.assertTrue(rnd.data["ice_servers"])  # STUN at least
        self.assertEqual(self._get(self.client_user).data["role"], "client")

    def test_outsiders_and_wrong_times_are_refused(self):
        self.assertEqual(self._get(self.outsider).data["code"], "not_yours")
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() + timedelta(hours=2))
        self.assertEqual(self._get(self.rnd).data["code"], "too_early")
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() - timedelta(hours=2))
        self.assertEqual(self._get(self.rnd).data["code"], "closed")

    def test_client_needs_to_have_paid(self):
        Invoice.objects.filter(appointment=self.appt).update(status="unpaid", paid_at=None)
        resp = self._get(self.client_user)
        self.assertEqual((resp.status_code, resp.data["code"]), (403, "not_paid"))
        self.assertEqual(self._get(self.rnd).status_code, 200)  # the RND can wait in the call

    def test_only_confirmed_video_consultations(self):
        Appointment.objects.filter(pk=self.appt.pk).update(type="in_person")
        self.assertEqual(self._get(self.rnd).data["code"], "not_video")
        Appointment.objects.filter(pk=self.appt.pk).update(type="video", status="completed")
        self.assertEqual(self._get(self.rnd).data["code"], "not_confirmed")

    @override_settings(CLOUDFLARE_TURN_KEY_ID="key", CLOUDFLARE_TURN_API_TOKEN="secret")
    def test_turn_credentials_come_from_cloudflare(self):
        fake = mock.Mock(status_code=201)
        fake.raise_for_status.return_value = None
        fake.json.return_value = {"iceServers": [{"urls": ["turn:turn.cloudflare.com:3478"], "username": "u", "credential": "p"}]}
        with mock.patch("scheduling.video_call.httpx.post", return_value=fake) as post:
            data = self._get(self.rnd).data
        self.assertEqual(data["ice_servers"][0]["username"], "u")
        self.assertIn("/turn/keys/key/credentials/generate-ice-servers", post.call_args.args[0])
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertLessEqual(post.call_args.kwargs["json"]["ttl"], 4 * 3600)


class CallSocketTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        _setup(self)

    def _socket(self, user):
        comm = WebsocketCommunicator(CallConsumer.as_asgi(), f"/ws/appointments/{self.appt.id}/call/")
        comm.scope["user"] = user
        comm.scope["url_route"] = {"kwargs": {"appointment_id": str(self.appt.id)}}
        return comm

    async def _join(self, user):
        comm = self._socket(user)
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        return comm, json.loads(await comm.receive_from())

    async def test_two_people_meet_and_pass_messages(self):
        rnd, hello = await self._join(self.rnd)
        self.assertEqual((hello["type"], hello["role"], hello["peers"]), ("welcome", "rnd", []))
        client, hello = await self._join(self.client_user)
        self.assertEqual([p["role"] for p in hello["peers"]], ["rnd"])
        self.assertEqual(json.loads(await rnd.receive_from())["type"], "peer-joined")

        await rnd.send_to(text_data=json.dumps({"type": "signal", "data": {"description": {"type": "offer", "sdp": "x"}}}))
        got = json.loads(await client.receive_from())
        self.assertEqual((got["type"], got["from"], got["data"]["description"]["type"]), ("signal", "rnd", "offer"))
        await client.send_to(text_data=json.dumps({"type": "media", "audio": False, "video": True}))
        got = json.loads(await rnd.receive_from())
        self.assertEqual((got["type"], got["audio"]), ("media", False))

        session = await database_sync_to_async(ConsultationSession.objects.get)(appointment=self.appt, video_provider="webrtc")
        self.assertEqual(session.session_status, "active")
        await client.disconnect()
        self.assertEqual(json.loads(await rnd.receive_from())["type"], "peer-left")
        await rnd.disconnect()
        session = await database_sync_to_async(ConsultationSession.objects.get)(pk=session.pk)
        self.assertEqual(session.session_status, "ended")

    async def test_outsider_is_refused(self):
        comm = self._socket(self.outsider)
        await comm.connect()
        msg = json.loads(await comm.receive_from())
        self.assertEqual((msg["type"], msg["code"]), ("denied", "not_yours"))
        await comm.disconnect()

    async def test_unpaid_client_is_refused(self):
        await database_sync_to_async(Invoice.objects.filter(appointment=self.appt).update)(status="unpaid", paid_at=None)
        comm = self._socket(self.client_user)
        await comm.connect()
        self.assertEqual(json.loads(await comm.receive_from())["code"], "not_paid")
        await comm.disconnect()

    async def test_opening_it_again_replaces_the_older_tab(self):
        first, _ = await self._join(self.rnd)
        second, _ = await self._join(self.rnd)
        self.assertEqual(json.loads(await first.receive_from())["type"], "replaced")
        client, hello = await self._join(self.client_user)
        self.assertEqual(len(hello["peers"]), 1)  # still one RND, not two
        for comm in (first, second, client):
            await comm.disconnect()
