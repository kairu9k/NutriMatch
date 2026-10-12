"""Jitsi Meet video consultation session service.

Uses the free public meet.jit.si server — no API key, no account, no
payment method required (unlike Daily.co, whose call UI gates on having a
card on file even within free-tier usage). Room creation is implicit:
Jitsi creates the room the moment the first participant loads the URL, so
"creating a room" here just means generating an unguessable room name.

Security notes:
 - Access control is URL secrecy only (meet.jit.si has no auth) — room
   names include a long random suffix so they can't be guessed. The real
   access gate is that ConsultationRoom.vue only reveals the URL after an
   authenticated appointment lookup confirms the viewer is the RND or
   client on that appointment.
 - There is no host/participant URL distinction on the public server, so
   both are the same URL — this removes the Daily.co host_url leak risk
   entirely rather than requiring extra care to avoid it.
"""

import secrets
import string


class VideoSessionError(Exception):
    pass


def _random_suffix(length=12):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class JitsiVideoService:
    BASE_URL = "https://meet.jit.si"

    def create_room(self, appointment) -> dict:
        """Generate a Jitsi room for the appointment.
        Returns {'external_session_id', 'host_url', 'participant_url'}.
        """
        room_name = f"nm-appt-{appointment.id}-{_random_suffix()}"
        room_url = f"{self.BASE_URL}/{room_name}"

        return {
            "external_session_id": room_name,
            "host_url": room_url,
            "participant_url": room_url,
        }

    def delete_room(self, external_session_id: str) -> bool:
        # No API to call — meet.jit.si rooms are ephemeral and clean
        # themselves up once everyone leaves.
        return True


def current_rnd_relationship(client, exclude_rnd_id=None):
    """One RND at a time (user's rule, 2026-10-12): the client's care
    relationship that blocks booking a *different* RND, or None.

    Blocks: an active relationship (until that RND discharges them), or a
    pending one that still has a booking waiting or coming up (a first
    booking the RND hasn't confirmed yet). A pending relationship whose
    booking was declined, cancelled or expired doesn't block."""
    from django.utils import timezone

    from .models import Appointment, RndClientRelationship

    qs = RndClientRelationship.objects.filter(client=client).select_related("rnd")
    if exclude_rnd_id is not None:
        qs = qs.exclude(rnd_id=exclude_rnd_id)
    active = qs.filter(status=RndClientRelationship.Status.ACTIVE).first()
    if active:
        return active
    return qs.filter(
        status=RndClientRelationship.Status.PENDING,
        appointments__status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        appointments__scheduled_at__gte=timezone.now(),
    ).distinct().first()
