"""RND onboarding after approval (2026-11-16, panel feedback: sign-up asks only
what the admin needs to approve; the rest is set up here, like the client's
onboarding). Nothing is saved until the RND presses Finish setup: one request
validates everything and saves it in one transaction.

  profile       {bio?, languages, consultation_fee, consultation_modes, clinic_address?}
  availability  [{day_of_week, start_time, end_time}, ...]   at least one block
  payout        {method, account_name, account_number, bank_name?}   optional
"""
from django.utils import timezone
from rest_framework import serializers

from core.models import AuditLog

from .models import User


def complete_rnd_onboarding(user, data):
    """Validates and saves the whole onboarding. Raises a DRF ValidationError
    with field errors keyed like the form (profile fields, availability, payout)."""
    from billing.payout_account import save_payout_account
    from profiles.hours import clean_availability_blocks
    from profiles.models import RndAvailabilitySchedule
    from profiles.serializers import RndProfileUpdateSerializer
    from core.ph_time import ph_today

    profile = user.rnd_profile
    errors = {}

    payload = dict(data.get("profile") or {})
    # what the RND has to give here, whatever was filled in at sign-up
    for key, message in (("consultation_fee", "Set your consultation fee."),
                         ("consultation_modes", "Offer at least one consultation format."),
                         ("languages", "Choose at least one language you can consult in.")):
        if payload.get(key) in (None, "", []):
            errors[key] = [message]
    serializer = RndProfileUpdateSerializer(profile, data=payload, partial=True)
    if not serializer.is_valid():
        errors.update(serializer.errors)

    blocks = []
    try:
        blocks = clean_availability_blocks(data.get("availability"))
        if not blocks:
            errors["availability"] = ["Add at least one block of weekly hours. Clients can only book inside them."]
    except serializers.ValidationError as exc:
        errors["availability"] = exc.detail if isinstance(exc.detail, list) else [exc.detail]

    if errors:
        raise serializers.ValidationError(errors)

    serializer.save()
    today = ph_today()
    user.availability_schedules.all().delete()  # nothing can be booked before onboarding, so replacing is safe
    RndAvailabilitySchedule.objects.bulk_create([
        RndAvailabilitySchedule(rnd=user, day_of_week=day, start_time=start, end_time=end, effective_from=today)
        for day, start, end in blocks
    ])

    payout = data.get("payout")
    if payout:
        try:
            save_payout_account(user, payout)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({"payout": exc.detail})

    user.onboarding_completed_at = timezone.now()
    user.save(update_fields=["onboarding_completed_at"])
    AuditLog.objects.create(user=user, action="rnd.onboarding_completed", table_name="rnd_profiles", record_id=profile.id,
                            new_values={"availability_blocks": len(blocks), "payout_added": bool(payout)})
    return user
