from django.db.models import Avg, Count
from rest_framework import serializers

from accounts.serializers import UserSerializer
from scheduling.models import Review

from .models import (
    CONSULTATION_MODES,
    ClientHealthProfile,
    ClientProfile,
    RndAvailabilitySchedule,
    RndLanguage,
    RndProfile,
)


class PublicReviewSerializer(serializers.ModelSerializer):
    """Reviews shown on an RND's public profile — first name + last-initial
    only, not the full UserSerializer, per this project's PII-minimization
    pattern (RA 10173)."""

    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "client_name", "rating", "comment", "created_at"]

    def get_client_name(self, obj):
        last_initial = f"{obj.client.last_name[0]}." if obj.client.last_name else ""
        return f"{obj.client.first_name} {last_initial}".strip()


class RndLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RndLanguage
        fields = ["id", "language_code", "language_name"]


class RndAvailabilityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RndAvailabilitySchedule
        fields = [
            "id", "day_of_week", "start_time", "end_time",
            "is_available", "effective_from", "effective_to",
        ]

    def validate(self, attrs):
        # Only enforced when both are present in this request — on a PATCH
        # that only touches one field, fall back to the existing instance's
        # other value so a partial update can't accidentally bypass this.
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start is not None and end is not None and end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs


class RndProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    languages = RndLanguageSerializer(source="user.languages", many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = RndProfile
        fields = [
            "id", "user", "prc_license_number", "prc_expiry_date", "specialization",
            "language_codes", "bio", "consultation_fee", "consultation_modes", "available_for_new_clients",
            "is_verified", "verified_at", "languages", "average_rating", "review_count",
        ]
        read_only_fields = ["is_verified", "verified_at"]

    def _review_aggregate(self, obj):
        if not hasattr(obj, "_review_aggregate_cache"):
            obj._review_aggregate_cache = Review.objects.filter(
                rnd_id=obj.user_id, is_public=True
            ).aggregate(avg_rating=Avg("rating"), review_count=Count("id"))
        return obj._review_aggregate_cache

    def get_average_rating(self, obj):
        return self._review_aggregate(obj)["avg_rating"]

    def get_review_count(self, obj):
        return self._review_aggregate(obj)["review_count"]


class RndProfileUpdateSerializer(serializers.ModelSerializer):
    """For the RND editing their own profile — excludes verification fields."""

    class Meta:
        model = RndProfile
        fields = [
            "specialization", "language_codes", "bio", "consultation_fee",
            "consultation_modes", "available_for_new_clients",
        ]

    def validate_consultation_fee(self, value):
        if value < 0:
            raise serializers.ValidationError("Consultation fee can't be negative.")
        return value

    def validate_consultation_modes(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Offer at least one consultation mode.")
        invalid = [m for m in value if m not in CONSULTATION_MODES]
        if invalid:
            raise serializers.ValidationError(f"Unknown mode(s): {', '.join(map(str, invalid))}.")
        # Keep a stable order and drop duplicates.
        return [m for m in CONSULTATION_MODES if m in value]


class ClientHealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientHealthProfile
        fields = [
            "id", "medical_conditions", "allergies",
            "dietary_restrictions", "health_goals", "religion", "notes",
        ]


class ClientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    health_profile = ClientHealthProfileSerializer(source="user.health_profile", read_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            "id", "user", "date_of_birth", "sex", "language_code",
            "address", "emergency_contact", "emergency_phone", "health_profile",
        ]


class ClientProfileUpdateSerializer(serializers.ModelSerializer):
    """For the client editing their own profile — excludes the linked user.
    medical_conditions lives on ClientHealthProfile; the first entry is the
    primary condition shown on the RND's patient list and client chart."""

    medical_conditions = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=True), required=False, allow_empty=True, max_length=10,
        write_only=True,
    )

    class Meta:
        model = ClientProfile
        fields = [
            "date_of_birth", "sex", "language_code", "address", "emergency_contact", "emergency_phone",
            "medical_conditions",
        ]

    def validate_medical_conditions(self, value):
        cleaned = []
        for item in value:
            item = item.strip()
            if item and item.lower() not in {c.lower() for c in cleaned}:
                cleaned.append(item)
        return cleaned

    def update(self, instance, validated_data):
        conditions = validated_data.pop("medical_conditions", None)
        instance = super().update(instance, validated_data)
        if conditions is not None:
            health_profile, _ = ClientHealthProfile.objects.get_or_create(user=instance.user)
            health_profile.medical_conditions = conditions or None
            health_profile.save(update_fields=["medical_conditions", "updated_at"])
        return instance
