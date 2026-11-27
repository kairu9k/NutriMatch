"""Demo mode for the defense (2026-11-27, user's call). Off unless the server has DEMO_MODE=true
(Render env var). Payment is never skipped (the adviser's rule): Pay still goes through the
payment provider (Xendit test mode, billing/xendit.py).

While it is on:
- A booking may start any time from now (no 45-minute lead), the RND may confirm and the client
  may pay up to the start (no 30 / 15 minute deadlines).
- The room opens as soon as the consultation is confirmed and paid (up to a day before).

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


def join_early_minutes() -> int:
    from .serializers import JOIN_EARLY_MINUTES

    return DEMO_JOIN_EARLY_MINUTES if demo_mode() else JOIN_EARLY_MINUTES
