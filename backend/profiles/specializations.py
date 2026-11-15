"""An RND's specializations (2026-11-16, panel feedback at the mock defense):
up to 3 picks from RND_SPECIALIZATIONS, one of them may be typed ("Other").
An RND who covers more than 3 areas picks General / Clinical Nutrition, which
stands alone.

They're kept in the existing RndProfile.specialization column as one text
joined with ", " (no listed name contains a comma, and typed ones can't), so
everything that shows the specialization keeps working unchanged."""
import re

from rest_framework import serializers

from .models import RND_SPECIALIZATIONS

MAX_SPECIALIZATIONS = 3
GENERAL = "General / Clinical Nutrition"
SEPARATOR = ", "
OTHER_MIN, OTHER_MAX = 3, 60
# letters (Filipino names too), spaces and a few joiners; never a comma
_OTHER_PATTERN = re.compile(r"[A-Za-zÀ-ÿÑñ][A-Za-zÀ-ÿÑñ .'&/-]*")


def _capitalize(name):
    """First letter of each word upper-case, the rest as typed (the same as the form does)."""
    return re.sub(r"(^|[ /-])([a-zà-ÿñ])", lambda m: m.group(1) + m.group(2).upper(), name)


def split_specializations(text):
    """The saved text back as a list."""
    return [s.strip() for s in (text or "").split(",") if s.strip()]


def clean_specializations(values):
    """Validates the picks and returns the text to save. Raises a
    ValidationError with a message the form can show."""
    if isinstance(values, str):
        values = [values]
    picks, others = [], []
    listed = {s.lower(): s for s in RND_SPECIALIZATIONS}
    for raw in values or []:
        name = re.sub(r"\s+", " ", str(raw or "")).strip()
        if not name:
            continue
        canonical = listed.get(name.lower())
        if canonical is None:
            if not (OTHER_MIN <= len(name) <= OTHER_MAX) or not _OTHER_PATTERN.fullmatch(name):
                raise serializers.ValidationError(
                    f"Type your specialization in letters, {OTHER_MIN} to {OTHER_MAX} characters, without commas."
                )
            name = _capitalize(name)
            others.append(name)
            canonical = name
        if canonical.lower() not in (p.lower() for p in picks):
            picks.append(canonical)
    if not picks:
        raise serializers.ValidationError("Pick at least one specialization.")
    if len(others) > 1:
        raise serializers.ValidationError("Type only one specialization of your own.")
    if GENERAL in picks and len(picks) > 1:
        raise serializers.ValidationError(f"{GENERAL} covers every area, so pick it on its own.")
    if len(picks) > MAX_SPECIALIZATIONS:
        raise serializers.ValidationError(
            f"Pick up to {MAX_SPECIALIZATIONS}. If you practise in more areas, choose {GENERAL}."
        )
    return SEPARATOR.join(picks)


def specialization_filter_regex(name):
    """Matches one whole pick inside the joined text (so "Renal Nutrition"
    doesn't also find "Pediatric Renal Nutrition")."""
    return r"(^|, )" + re.escape(name) + r"(,|$)"
