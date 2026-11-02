"""Who attended a video consultation (2026-11-02, user's plan).

The call's signaling socket (scheduling/consumers.py) tells us when each
person joins and leaves; we keep the first join, the last leave and how long
both were in the call together. Only these times are stored, never anything
from the call itself (RA 10173). It decides whether the RND may mark the
client as a no-show (not once the client joined) and whether the client may
report the RND absent, and it's shown to the admin, the RND and the client."""

from django.db import transaction
from django.utils import timezone

ROLES = ("rnd", "client")


def record_presence(appointment_id, role, joined, present_roles, now=None):
    """`role` joined (joined=True) or left; `present_roles` = who is in the
    call after this change."""
    from .models import Appointment

    now = now or timezone.now()
    with transaction.atomic():
        a = Appointment.objects.select_for_update().filter(pk=appointment_id).first()
        if a is None or role not in ROLES:
            return
        fields = []
        if joined and getattr(a, f"{role}_joined_at") is None:
            setattr(a, f"{role}_joined_at", now)
            fields.append(f"{role}_joined_at")
        since = getattr(a, f"{role}_in_since")
        if joined and since is None:
            setattr(a, f"{role}_in_since", now)
            fields.append(f"{role}_in_since")
        if not joined:
            setattr(a, f"{role}_left_at", now)
            if since is not None:
                setattr(a, f"{role}_seconds", getattr(a, f"{role}_seconds") + max(0, int((now - since).total_seconds())))
                setattr(a, f"{role}_in_since", None)
            fields += [f"{role}_left_at", f"{role}_seconds", f"{role}_in_since"]
        both = set(ROLES) <= set(present_roles)
        if both and a.together_since is None:
            a.together_since = now
            fields.append("together_since")
        elif not both and a.together_since is not None:
            a.together_seconds += max(0, int((now - a.together_since).total_seconds()))
            a.together_since = None
            fields += ["together_seconds", "together_since"]
        if fields:
            a.save(update_fields=fields)


def together_minutes(a, now=None):
    seconds = a.together_seconds
    if a.together_since is not None:
        seconds += max(0, int(((now or timezone.now()) - a.together_since).total_seconds()))
    return seconds // 60


def minutes_in_call(a, role, now=None):
    """One person's total minutes in the call, including right now."""
    seconds = getattr(a, f"{role}_seconds")
    since = getattr(a, f"{role}_in_since")
    if since is not None:
        seconds += max(0, int(((now or timezone.now()) - since).total_seconds()))
    return seconds // 60


def attendance_state(a):
    """both | rnd_only | client_only | none (None for consultations that
    aren't video calls, where nothing is recorded)."""
    if a.type != a.Type.VIDEO:
        return None
    rnd, client = a.rnd_joined_at is not None, a.client_joined_at is not None
    return "both" if rnd and client else "rnd_only" if rnd else "client_only" if client else "none"


def attendance_line(a, now=None):
    """One plain sentence, for the admin and the dispute review."""
    from .views import format_ph_time

    state = attendance_state(a)
    if state is None:
        return "In-person consultation, so no attendance is recorded."
    if state == "none":
        return "Neither person joined the video call."
    if state == "both":
        mins = together_minutes(a, now)
        return (f"Both attended. RND joined {format_ph_time(a.rnd_joined_at)} (in the call {minutes_in_call(a, 'rnd', now)} min), "
                f"client {format_ph_time(a.client_joined_at)} ({minutes_in_call(a, 'client', now)} min), together {mins} min.")
    if state == "rnd_only":
        return (f"Only the RND joined ({format_ph_time(a.rnd_joined_at)}, in the call {minutes_in_call(a, 'rnd', now)} min). "
                "The client never joined.")
    return (f"Only the client joined ({format_ph_time(a.client_joined_at)}, in the call {minutes_in_call(a, 'client', now)} min). "
            "The RND never joined.")


def attendance_payload(a, now=None):
    state = attendance_state(a)
    if state is None:
        return None
    return {
        "state": state,
        "rnd_joined_at": a.rnd_joined_at, "client_joined_at": a.client_joined_at,
        "rnd_left_at": a.rnd_left_at, "client_left_at": a.client_left_at,
        "together_minutes": together_minutes(a, now),
        "rnd_minutes": minutes_in_call(a, "rnd", now), "client_minutes": minutes_in_call(a, "client", now),
        "rnd_in_call": a.rnd_in_since is not None, "client_in_call": a.client_in_since is not None,
        "in_call_now": a.together_since is not None,
        "line": attendance_line(a, now),
    }


def dispute_payload(a, now=None):
    """The client's no-show dispute, and until when they can open one."""
    from datetime import timedelta

    from .serializers import DISPUTE_DAYS

    if a.status != a.Status.NO_SHOW:
        return None
    until = (a.completed_at + timedelta(days=DISPUTE_DAYS)) if a.completed_at else None
    now = now or timezone.now()
    return {
        "open_until": until,
        "can_open": a.dispute_opened_at is None and until is not None and now < until,
        "opened_at": a.dispute_opened_at, "reason": a.dispute_reason,
        "resolved_at": a.dispute_resolved_at, "outcome": a.dispute_outcome, "note": a.dispute_note,
    }
