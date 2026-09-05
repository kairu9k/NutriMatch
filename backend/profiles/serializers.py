from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import ClientHealthProfile, ClientProfile, RndAvailabilitySchedule, RndLanguage, RndProfile


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


class RndProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    languages = RndLanguageSerializer(source="user.languages", many=True, read_only=True)

    class Meta:
        model = RndProfile
        fields = [
            "id", "user", "prc_license_number", "prc_expiry_date", "specialization",
            "language_codes", "bio", "consultation_fee", "available_for_new_clients",
            "is_verified", "verified_at", "languages",
        ]
        read_only_fields = ["is_verified", "verified_at"]


class RndProfileUpdateSerializer(serializers.ModelSerializer):
    """For the RND editing their own profile — excludes verification fields."""

    class Meta:
        model = RndProfile
        fields = ["specialization", "language_codes", "bio", "consultation_fee", "available_for_new_clients"]


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
    """For the client editing their own profile — excludes the linked user."""

    class Meta:
        model = ClientProfile
        fields = ["date_of_birth", "sex", "language_code", "address", "emergency_contact", "emergency_phone"]
