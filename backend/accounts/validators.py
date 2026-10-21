import re

from django.core.exceptions import ValidationError
from rest_framework import serializers

# Letters in any language (so ñ, é… work), plus the separators real names
# use: spaces, hyphens, apostrophes and periods ("Dela Cruz", "O'Neil",
# "Ma. Theresa"). No digits or other symbols.
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ .'\-]+[^\W\d_]+)*\.?$")


# The first letter of each word ("juan dela cruz" → "Juan Dela Cruz",
# "o'neil" → "O'Neil"); the rest is kept as typed, so "McDonald" stays.
_WORD_START_RE = re.compile(r"(^|[ .'\-])([^\W\d_])")


def validate_person_name(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise serializers.ValidationError("This field may not be blank.")
    if not _NAME_RE.match(value):
        raise serializers.ValidationError(
            "Use letters only — spaces, hyphens (-), apostrophes (') and periods (.) are allowed, numbers are not."
        )
    return _WORD_START_RE.sub(lambda m: m.group(1) + m.group(2).upper(), value)


# Minimum ages to hold an account. Clients: 18 — a minor's health data needs
# a parent/guardian's consent under RA 10173 and there's no guardian flow.
# RNDs: 21 — a licensed RND has a 4-year nutrition degree and passed the PRC
# board exam. The registration form (RegisterFlow.vue) uses the same numbers.
MIN_CLIENT_AGE = 18
MIN_RND_AGE = 21


def age_on(birth_date, today=None):
    from core.ph_time import ph_today

    today = today or ph_today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def validate_birth_date(value, min_age=None):
    """A date of birth can't be in the future (or implausibly old), and the
    person must be at least `min_age` years old when given."""
    if value is None:
        return value
    from core.ph_time import ph_today

    if value > ph_today():
        raise serializers.ValidationError("Date of birth can't be in the future.")
    if value.year < 1900:
        raise serializers.ValidationError("Enter a valid date of birth.")
    if min_age is not None and age_on(value) < min_age:
        raise serializers.ValidationError(f"You must be at least {min_age} years old to register.")
    return value


def validate_client_birth_date(value):
    return validate_birth_date(value, MIN_CLIENT_AGE)


def validate_rnd_birth_date(value):
    return validate_birth_date(value, MIN_RND_AGE)


class PasswordComplexityValidator:
    """Django password validator (AUTH_PASSWORD_VALIDATORS): at least one
    uppercase letter, one lowercase letter, one number and one special
    character. Length is MinimumLengthValidator's job. The registration
    form shows the same rules as a live checklist (RegisterFlow.vue)."""

    RULES = [
        (re.compile(r"[A-Z]"), "an uppercase letter"),
        (re.compile(r"[a-z]"), "a lowercase letter"),
        (re.compile(r"\d"), "a number"),
        (re.compile(r"[^A-Za-z0-9\s]"), "a special character (e.g. ! @ # $)"),
    ]

    def validate(self, password, user=None):
        missing = [label for pattern, label in self.RULES if not pattern.search(password)]
        if missing:
            raise ValidationError(
                "Your password must include " + ", ".join(missing) + ".",
                code="password_too_simple",
            )

    def get_help_text(self):
        return "Your password must include an uppercase letter, a lowercase letter, a number and a special character."
