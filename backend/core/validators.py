import re

import phonenumbers
from django.db import models
from phonenumbers import geocoder
from rest_framework import serializers

_BLOOD_PRESSURE = re.compile(r"^\d{2,3}/\d{2,3}$")


class NonNegativeNumbersMixin:
    """For ModelSerializers: every numeric model field (decimal/integer/
    float) refuses values below zero — measurements, targets and amounts
    are never negative. Choice-backed integers (e.g. day_of_week) are left
    alone; a field that already sets its own min_value keeps it."""

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super().build_standard_field(field_name, model_field)
        numeric = isinstance(model_field, (models.DecimalField, models.IntegerField, models.FloatField))
        if numeric and "choices" not in field_kwargs and "min_value" not in field_kwargs:
            field_kwargs["min_value"] = 0
        return field_class, field_kwargs


def validate_blood_pressure(value):
    """Blood pressure is stored as "systolic/diastolic" text (e.g. "120/80")
    — digits only on both sides. Blank/None means not recorded."""
    if value in (None, ""):
        return value
    value = value.replace(" ", "")
    if not _BLOOD_PRESSURE.match(value):
        raise serializers.ValidationError("Enter blood pressure as two numbers, e.g. 120/80.")
    systolic, diastolic = (int(x) for x in value.split("/"))
    if not (60 <= systolic <= 260 and 30 <= diastolic <= 160):
        raise serializers.ValidationError("Blood pressure must be 60–260 over 30–160 mmHg.")
    if diastolic >= systolic:
        raise serializers.ValidationError("The first number (systolic) must be higher than the second.")
    return value


_MOBILE_TYPES = (phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE)


def _country_name(region):
    return geocoder._region_display_name(region, "en") or region


def validate_phone(value):
    """A mobile number from any country, saved in E.164 (+639171234567).
    Each country's length and prefixes come from Google's libphonenumber
    data (`phonenumbers`), the same data the frontend's PhoneInput uses.
    A number without a + is read as Philippine (0917 123 4567). Landlines
    are refused — the number is for reaching the person. Blank/None means
    not given (the field is optional)."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        number = phonenumbers.parse(value, "PH")
    except phonenumbers.NumberParseException:
        raise serializers.ValidationError("Enter a mobile number, e.g. +63 917 123 4567.")
    region = phonenumbers.region_code_for_number(number) or phonenumbers.region_code_for_country_code(number.country_code)
    if region in (None, "ZZ"):
        raise serializers.ValidationError("Unknown country code. Pick the country and enter the number.")
    if not phonenumbers.is_valid_number(number) or phonenumbers.number_type(number) not in _MOBILE_TYPES:
        example = phonenumbers.example_number_for_type(region, phonenumbers.PhoneNumberType.MOBILE)
        hint = f", e.g. {phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}" if example else ""
        raise serializers.ValidationError(f"Enter a valid {_country_name(region)} mobile number{hint}.")
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
