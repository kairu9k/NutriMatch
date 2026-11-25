"""A client's health conditions (2026-11-23, adviser: a client can have more
than one). Stored as a list in ClientHealthProfile.medical_conditions; no
entry is "primary". Picked as chips at sign-up, in onboarding and in Profile
Settings (frontend components/ConditionPicker.vue); "Other" lets the client
type their own."""

import re

from rest_framework import serializers

# what the chips offer; anything else is the client's own words
CONDITION_CHOICES = ("Hypertension", "Type 2 Diabetes", "Obesity management", "Renal nutrition")
# labels the old single dropdown could send that mean "no condition"
NOT_A_CONDITION = {"other", "none", "none / not sure", "not sure"}
MAX_LENGTH = 100
_WORDS = re.compile(r"^[A-Za-zÀ-ÿÑñ0-9][A-Za-zÀ-ÿÑñ0-9 .,'&/()+-]*$")


def clean_conditions(values):
    """Trim, drop empties, "Other"/"None" and repeats (ignoring case), and
    check each is plain words. Raises a ValidationError with the reason."""
    cleaned = []
    for item in values or []:
        item = re.sub(r"\s+", " ", str(item)).strip()
        if not item or item.lower() in NOT_A_CONDITION or item.lower() in {c.lower() for c in cleaned}:
            continue
        if len(item) < 2 or len(item) > MAX_LENGTH or not _WORDS.match(item):
            raise serializers.ValidationError(
                f'"{item[:40]}" isn\'t a condition we can save. Use letters and numbers, 2 to {MAX_LENGTH} characters.')
        cleaned.append(item)
    return cleaned
