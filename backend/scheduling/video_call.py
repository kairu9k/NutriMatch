"""NutriMatch's own 1-on-1 video call (WebRTC, 2026-10-26, user's call).

The two browsers connect directly (encrypted between them); NutriMatch only
introduces them: the signaling socket (scheduling/consumers.py CallConsumer)
passes offers, answers and ICE candidates, and the call config hands out
STUN + TURN servers. TURN is Cloudflare's (free tier, 1,000 GB/month relay):
its API token stays on the server, and the browser gets credentials that
expire when the join window closes. Calls are not recorded (RA 10173).

Who may join (same rules as the old room link): the appointment's RND or
client, a confirmed video consultation, inside the join window (15 min before
the start to the scheduled end), and the client only once it's paid. At most
two people in a call. There's no overtime (2026-11-16): the room warns both
people 15 and 5 minutes before the end, then the server ends the call at the
scheduled end (scheduling/consumers.py)."""

from datetime import timedelta

import httpx
from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment

MAX_PEOPLE = 2
# without TURN (not configured or Cloudflare down) calls still work on friendly networks
FALLBACK_ICE = [{"urls": ["stun:stun.cloudflare.com:3478", "stun:stun.l.google.com:19302"]}]


class CallDenied(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def end_of(appointment):
    from .serializers import DEFAULT_SESSION_MINUTES

    return appointment.scheduled_at + timedelta(minutes=appointment.duration_minutes or DEFAULT_SESSION_MINUTES)


def room_opens_at(appointment):
    """When the consultation room opens: 15 minutes before the start (a day before in demo mode).
    An in-person visit's room opens from the start of its day in Philippine time (2026-11-27, user's
    call: a client who arrives early can be seen, and the RND can start the NCP, right away)."""
    from datetime import datetime, time

    from core.ph_time import PH_TZ

    from .demo import join_early_minutes

    start = appointment.scheduled_at
    opens = start - timedelta(minutes=join_early_minutes())
    if appointment.type == Appointment.Type.IN_PERSON:
        day_start = datetime.combine(start.astimezone(PH_TZ).date(), time.min, tzinfo=PH_TZ)
        opens = min(opens, day_start)
    return opens


def join_window(appointment):
    from .serializers import DEFAULT_SESSION_MINUTES, JOIN_LATE_MINUTES

    start = appointment.scheduled_at
    end = start + timedelta(minutes=appointment.duration_minutes or DEFAULT_SESSION_MINUTES)
    return room_opens_at(appointment), end + timedelta(minutes=JOIN_LATE_MINUTES)


def call_access(user, appointment_id, now=None):
    """(appointment, role) if `user` may be in this call now, else CallDenied."""
    from billing.services import is_appointment_paid

    if not getattr(user, "is_authenticated", False):
        raise CallDenied("not_signed_in", "Sign in to join the call.")
    appointment = (Appointment.objects.select_related("relationship__rnd", "relationship__client")
                   .filter(pk=appointment_id).first())
    rel = appointment.relationship if appointment else None
    if rel is None or user.id not in (rel.rnd_id, rel.client_id):
        raise CallDenied("not_yours", "This isn't your consultation.")
    role = "rnd" if user.id == rel.rnd_id else "client"
    if appointment.type != Appointment.Type.VIDEO:
        raise CallDenied("not_video", "This consultation isn't a video call.")
    if appointment.status != Appointment.Status.CONFIRMED:
        raise CallDenied("not_confirmed", "This consultation isn't confirmed, so the call isn't open.")
    opens, closes = join_window(appointment)
    now = now or timezone.now()
    if now < opens:
        raise CallDenied("too_early", "The call opens 15 minutes before the start.")
    if now > closes:
        raise CallDenied("closed", "The call closed at the scheduled end.")
    if role == "client" and not is_appointment_paid(appointment):
        raise CallDenied("not_paid", "Pay for the consultation to join the call.")
    return appointment, role


def ice_servers(appointment):
    """STUN + TURN for the browser. TURN credentials last until the join
    window closes (at least 10 minutes, at most 4 hours)."""
    key_id = (getattr(settings, "CLOUDFLARE_TURN_KEY_ID", "") or "").strip()
    token = (getattr(settings, "CLOUDFLARE_TURN_API_TOKEN", "") or "").strip()
    if not (key_id and token):
        return FALLBACK_ICE
    _, closes = join_window(appointment)
    ttl = int(min(max((closes - timezone.now()).total_seconds(), 600), 4 * 3600))
    try:
        resp = httpx.post(
            f"https://rtc.live.cloudflare.com/v1/turn/keys/{key_id}/credentials/generate-ice-servers",
            headers={"Authorization": f"Bearer {token}"}, json={"ttl": ttl}, timeout=10,
        )
        resp.raise_for_status()
        servers = resp.json().get("iceServers")
    except (httpx.HTTPError, ValueError):
        return FALLBACK_ICE
    if isinstance(servers, dict):
        servers = [servers]
    return servers or FALLBACK_ICE


def mark_started(appointment_id):
    """Both people are in: the call has started (once)."""
    from .models import ConsultationSession

    session = (ConsultationSession.objects.filter(appointment_id=appointment_id,
                                                  video_provider=ConsultationSession.VideoProvider.WEBRTC)
               .order_by("-id").first())
    if session is None:
        session = ConsultationSession.objects.create(appointment_id=appointment_id,
                                                     video_provider=ConsultationSession.VideoProvider.WEBRTC)
    if session.session_started_at is None:
        session.session_started_at = timezone.now()
    session.session_status = ConsultationSession.SessionStatus.ACTIVE
    session.session_ended_at = None
    session.save(update_fields=["session_started_at", "session_status", "session_ended_at"])


def mark_ended(appointment_id):
    """Everyone left: the call ended (it can start again if they rejoin)."""
    from .models import ConsultationSession

    ConsultationSession.objects.filter(
        appointment_id=appointment_id, video_provider=ConsultationSession.VideoProvider.WEBRTC,
        session_status=ConsultationSession.SessionStatus.ACTIVE,
    ).update(session_status=ConsultationSession.SessionStatus.ENDED, session_ended_at=timezone.now())


# ---- REST: what the browser needs before it opens the call -----------------


class CallConfigView(APIView):
    """GET /api/appointments/<id>/call-config/ — the ICE servers (STUN, and
    TURN with short-lived credentials), who the other person is, and when the
    call closes. Same access rules as the signaling socket."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            appointment, role = call_access(request.user, pk)
        except CallDenied as denied:
            return Response({"detail": denied.message, "code": denied.code}, status=403)
        rel = appointment.relationship
        other = rel.client if role == "rnd" else rel.rnd
        _, closes = join_window(appointment)
        return Response({
            "role": role,
            "ice_servers": ice_servers(appointment),
            "other": {"name": other.full_name, "profile_photo": other.profile_photo, "role": "client" if role == "rnd" else "rnd"},
            "closes_at": closes,
            "socket_path": f"/ws/appointments/{appointment.id}/call/",
        })
