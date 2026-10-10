"""Shared test helpers: an RND that can actually use the app is approved and
fully set up (fee, bio, availability); a client that can book has finished
onboarding. Tests written before onboarding existed use these to build the
same kind of user the app now requires."""

from datetime import time
from decimal import Decimal

from django.utils import timezone

TEST_BIO = "Registered Nutritionist-Dietitian helping clients build realistic, sustainable eating habits."


def approve_rnd(user, *, availability=True, **profile_fields):
    """Make `user` (role rnd) an approved, bookable RND. `availability=True`
    adds an all-week 00:00-23:59 schedule so booking-time rules don't get
    in the way of tests that aren't about them."""
    from profiles.models import RndAvailabilitySchedule, RndProfile

    profile, _ = RndProfile.objects.get_or_create(
        user=user, defaults={"prc_license_number": f"PRC-{user.pk}"}
    )
    profile.is_verified = True
    profile.review_status = RndProfile.ReviewStatus.APPROVED
    profile.verified_at = profile.verified_at or timezone.now()
    if not (profile.bio or "").strip():
        profile.bio = TEST_BIO
    if (profile.consultation_fee or 0) < 100:
        profile.consultation_fee = Decimal("800.00")
    for key, value in profile_fields.items():
        setattr(profile, key, value)
    profile.save()
    if availability and not user.availability_schedules.exists():
        today = timezone.now().date()
        RndAvailabilitySchedule.objects.bulk_create([
            RndAvailabilitySchedule(rnd=user, day_of_week=d, start_time=time(0, 0), end_time=time(23, 59), effective_from=today)
            for d in range(7)
        ])
    if user.onboarding_completed_at is None:
        user.onboarding_completed_at = timezone.now()
        user.save(update_fields=["onboarding_completed_at"])
    # The caller's `user` may still have the unapproved profile cached.
    user._state.fields_cache.pop("rnd_profile", None)
    return user


def onboard_client(user):
    """Mark a client as having finished onboarding (so they can book)."""
    if user.onboarding_completed_at is None:
        user.onboarding_completed_at = timezone.now()
        user.save(update_fields=["onboarding_completed_at"])
    return user
