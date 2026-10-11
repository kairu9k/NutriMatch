import re

from django.db import models
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
