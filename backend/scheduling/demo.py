"""Demo mode for the defense (2026-11-27, user's call). Off unless the server has DEMO_MODE=true
(Render env var). Payment is never skipped (the adviser's rule): Pay still goes through the
payment provider (Xendit test mode, billing/xendit.py).

While it is on:
- A booking may start any time from now (no 45-minute lead), the RND may confirm and the client
  may pay up to the start (no 30 / 15 minute deadlines).
- The room opens as soon as the consultation is confirmed and paid (up to a day before).
- Rescheduling works closer to the time: either side can move a consultation or a request until
  30 minutes before it (not 2 hours), to a time at least 1 hour ahead, and a waiting answer runs
  until 15 minutes before.

Everything else (the call, closing rules, NCP, summaries, refunds) is unchanged. Turning the
env var off restores every normal rule; nothing is stored about the mode itself.
"""
from django.conf import settings

DEMO_JOIN_EARLY_MINUTES = 24 * 60


def demo_mode() -> bool:
    return bool(getattr(settings, "DEMO_MODE", False))


def booking_lead_minutes() -> int:
    from .serializers import MIN_BOOKING_LEAD_MINUTES

    return 0 if demo_mode() else MIN_BOOKING_LEAD_MINUTES


def confirm_by_minutes() -> int:
    from .serializers import CONFIRM_BY_MINUTES

    return 0 if demo_mode() else CONFIRM_BY_MINUTES


def pay_by_minutes() -> int:
    from .serializers import PAY_BY_MINUTES

    return 0 if demo_mode() else PAY_BY_MINUTES


def reschedule_cutoff_minutes() -> int:
    from .reschedule import REQUEST_CUTOFF_MINUTES

    return 30 if demo_mode() else REQUEST_CUTOFF_MINUTES


def reschedule_lead_minutes() -> int:
    from .reschedule import MIN_LEAD_MINUTES

    return 60 if demo_mode() else MIN_LEAD_MINUTES


def answer_before_minutes() -> int:
    from .reschedule import ANSWER_BEFORE_MINUTES

    return 15 if demo_mode() else ANSWER_BEFORE_MINUTES


def call_counts_as_held(a, now=None) -> bool:
    """A video consultation can be marked complete: both were in the call together for
    MIN_TOGETHER_MINUTES (5); in demo mode as soon as both have joined (2026-11-28, the
    adviser: a short demo call couldn't be finished)."""
    from .attendance import together_minutes
    from .serializers import MIN_TOGETHER_MINUTES

    if demo_mode():
        return a.rnd_joined_at is not None and a.client_joined_at is not None
    return together_minutes(a, now) >= MIN_TOGETHER_MINUTES


def join_early_minutes() -> int:
    from .serializers import JOIN_EARLY_MINUTES

    return DEMO_JOIN_EARLY_MINUTES if demo_mode() else JOIN_EARLY_MINUTES
